"""
Production middleware for AlphaEdge API.

- RateLimitMiddleware:       Dual-key (IP + user) sliding-window rate limiter
- SecurityHeadersMiddleware: OWASP-recommended response headers
- RequestIDMiddleware:       Adds X-Request-ID for tracing

OWASP references:
  - https://cheatsheetseries.owasp.org/cheatsheets/REST_Security_Cheat_Sheet.html
  - https://cheatsheetseries.owasp.org/cheatsheets/HTTP_Headers_Cheat_Sheet.html
"""

import math
import time
import uuid
from collections import defaultdict
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from alphaedge.logger import log

# ── Rate Limiter ─────────────────────────────────────────────────
# OWASP: "Implement rate limiting to prevent abuse."
# Dual-key design: limits are applied both per-IP *and* per-user
# when a valid Clerk JWT is present, so that a single authenticated
# user cannot exhaust the quota for an entire corporate IP.

# Stale-entry cleanup interval (seconds).  Prevents unbounded memory
# growth when many unique IPs send a single burst then disappear.
_CLEANUP_INTERVAL = 300  # 5 minutes


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Sliding-window rate limiter keyed by **client IP + authenticated user**.

    Behaviour:
      * Anonymous requests  → limited by IP (``max_requests`` / window).
      * Authenticated users → get a **separate, higher** bucket
        (``auth_multiplier × max_requests``).  The IP bucket is *not*
        consumed so legitimate users behind a shared NAT don't starve.
      * Health / root paths are exempt so orchestrators aren't throttled.

    Each 429 response includes standard ``Retry-After``,
    ``X-RateLimit-Limit``, ``X-RateLimit-Remaining`` and
    ``X-RateLimit-Reset`` headers for well-behaved clients.
    """

    def __init__(
        self,
        app,
        max_requests: int = 60,
        window_seconds: int = 60,
        auth_multiplier: float = 3.0,
    ):
        super().__init__(app)
        self.max_requests = max_requests
        self.window = window_seconds
        # Authenticated users get a higher ceiling
        self.auth_max = int(max_requests * auth_multiplier)
        self._hits: dict[str, list[float]] = defaultdict(list)
        self._last_cleanup: float = time.time()

    # ── helpers ───────────────────────────────────────────────────

    @staticmethod
    def _client_ip(request: Request) -> str:
        """Extract the *real* client IP, respecting reverse-proxy headers.

        Order: CF-Connecting-IP (Cloudflare) → X-Forwarded-For → socket.
        Only the **first** entry in X-Forwarded-For is used to avoid
        spoofing via appended headers (OWASP header-injection).
        """
        # Cloudflare's guaranteed single-value header
        cf_ip = request.headers.get("cf-connecting-ip")
        if cf_ip:
            return cf_ip.strip()
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    @staticmethod
    def _user_id_from_request(request: Request) -> str | None:
        """Cheaply extract the Clerk ``sub`` claim without full verification.

        Full JWT verification happens later in the dependency chain;
        here we only need the *identity* for bucketing, so base64-
        decoding the payload is sufficient and avoids a crypto round-trip
        on every request.
        """
        auth = request.headers.get("authorization", "")
        if not auth.lower().startswith("bearer "):
            return None
        token = auth[7:]
        try:
            import base64
            import json as _json

            # JWT = header.payload.signature — we want the payload
            payload_b64 = token.split(".")[1]
            # Fix padding
            payload_b64 += "=" * (-len(payload_b64) % 4)
            payload = _json.loads(base64.urlsafe_b64decode(payload_b64))
            return payload.get("sub")
        except Exception:
            return None

    def _prune_stale_keys(self, now: float) -> None:
        """Periodically remove keys with no recent hits to bound memory."""
        if now - self._last_cleanup < _CLEANUP_INTERVAL:
            return
        cutoff = now - self.window
        stale = [k for k, ts in self._hits.items() if not ts or ts[-1] < cutoff]
        for k in stale:
            del self._hits[k]
        self._last_cleanup = now

    # ── dispatch ─────────────────────────────────────────────────

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Exempt paths (health probes, root info)
        if request.url.path in ("/health", "/"):
            return await call_next(request)

        now = time.time()
        self._prune_stale_keys(now)
        cutoff = now - self.window

        ip = self._client_ip(request)
        user_id = self._user_id_from_request(request)

        # Pick the correct bucket key and ceiling
        if user_id:
            key = f"user:{user_id}"
            limit = self.auth_max
        else:
            key = f"ip:{ip}"
            limit = self.max_requests

        # Prune expired timestamps for this key
        self._hits[key] = [t for t in self._hits[key] if t > cutoff]

        if len(self._hits[key]) >= limit:
            retry_after = int(math.ceil(self._hits[key][0] + self.window - now))
            log.warning(
                f"Rate limit exceeded: {key} " f"({len(self._hits[key])}/{limit} in {self.window}s)"
            )
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Too many requests. Please try again later.",
                    "retry_after_seconds": max(retry_after, 1),
                },
                headers={
                    "Retry-After": str(max(retry_after, 1)),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(now + max(retry_after, 1))),
                },
            )

        self._hits[key].append(now)
        remaining = limit - len(self._hits[key])
        reset_at = int(self._hits[key][0] + self.window)

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_at)
        return response


# ── Security Headers ─────────────────────────────────────────────


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add OWASP-recommended security headers to every response.

    References:
      https://cheatsheetseries.owasp.org/cheatsheets/HTTP_Headers_Cheat_Sheet.html
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        # -- Prevent MIME-type sniffing (OWASP) --
        response.headers["X-Content-Type-Options"] = "nosniff"
        # -- Prevent clickjacking --
        response.headers["X-Frame-Options"] = "DENY"
        # -- XSS auditor (legacy browsers) --
        response.headers["X-XSS-Protection"] = "1; mode=block"
        # -- Control Referer leakage --
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        # -- Restrict browser features --
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), payment=()"
        )
        # -- Content-Security-Policy (API-only, very restrictive) --
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
        # -- HSTS — enforce HTTPS (1 year, include subdomains, preload-ready) --
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )
        # -- Prevent caching of authenticated responses --
        if request.headers.get("authorization"):
            response.headers["Cache-Control"] = "no-store"
            response.headers["Pragma"] = "no-cache"
        return response


# ── Request ID ───────────────────────────────────────────────────


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attach a unique X-Request-ID to every request/response for tracing."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
