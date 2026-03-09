"""
Clerk authentication middleware & utilities for AlphaEdge.

Uses Clerk's JWT verification to protect API routes.
Clerk issues JWTs — we verify them server-side using the JWKS endpoint.

Docs: https://clerk.com/docs/backend-requests/handling/manual-jwt

Security:
  - JWKS responses cached (1 h) to limit outbound requests.
  - Token parsing errors logged but never echoed to clients (OWASP A07).
  - user_id is validated before being interpolated into Clerk API URL.
"""

import re
import time
from typing import Optional

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from alphaedge.config import settings
from alphaedge.logger import log

# ── Bearer scheme ────────────────────────────────────────────────
_bearer = HTTPBearer(auto_error=False)


class ClerkUser(BaseModel):
    """Minimal representation of an authenticated Clerk user."""

    user_id: str
    email: Optional[str] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    image_url: Optional[str] = None
    metadata: dict = {}


# ── JWKS cache ───────────────────────────────────────────────────
_jwks_cache: dict = {}
_jwks_fetched_at: float = 0
JWKS_TTL = 3600  # re-fetch keys every hour


def _get_jwks() -> dict:
    """Fetch Clerk's JWKS (JSON Web Key Set) with caching."""
    global _jwks_cache, _jwks_fetched_at

    if _jwks_cache and (time.time() - _jwks_fetched_at < JWKS_TTL):
        return _jwks_cache

    jwks_url = f"https://{settings.clerk_domain}/.well-known/jwks.json"
    try:
        resp = httpx.get(jwks_url, timeout=10)
        resp.raise_for_status()
        _jwks_cache = resp.json()
        _jwks_fetched_at = time.time()
        log.debug("Clerk JWKS refreshed")
        return _jwks_cache
    except Exception as e:
        log.error(f"Failed to fetch Clerk JWKS: {e}")
        if _jwks_cache:
            return _jwks_cache  # stale is better than nothing
        raise HTTPException(status_code=503, detail="Auth service unavailable")


def _verify_clerk_token(token: str) -> dict:
    """
    Verify a Clerk-issued JWT.

    Uses PyJWT + the JWKS fetched from Clerk to do RS256 verification.
    """
    try:
        import jwt as pyjwt
        from jwt import PyJWKClient

        jwks_url = f"https://{settings.clerk_domain}/.well-known/jwks.json"
        jwk_client = PyJWKClient(jwks_url, cache_keys=True)
        signing_key = jwk_client.get_signing_key_from_jwt(token)

        payload = pyjwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            options={"verify_aud": False},  # Clerk doesn't always set aud
            issuer=f"https://{settings.clerk_domain}",
        )
        return payload
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except pyjwt.InvalidTokenError as e:
        # OWASP: Do not leak token-parsing details to the client.
        log.warning(f"Invalid Clerk token: {e}")
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    except Exception as e:
        log.error(f"Clerk token verification error: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")


# ── FastAPI dependencies ─────────────────────────────────────────


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> ClerkUser:
    """
    Dependency that extracts and verifies the Clerk JWT from the
    Authorization header. Returns a ClerkUser on success, raises 401
    otherwise.
    """
    if not settings.enable_clerk_auth:
        # Auth disabled — return anonymous user (dev mode)
        return ClerkUser(user_id="anonymous", email="dev@alphaedge.local")

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = _verify_clerk_token(credentials.credentials)

    return ClerkUser(
        user_id=payload.get("sub", ""),
        email=payload.get("email"),
        username=payload.get("username"),
        first_name=payload.get("first_name"),
        last_name=payload.get("last_name"),
        image_url=payload.get("image_url"),
        metadata=payload.get("public_metadata", {}),
    )


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> Optional[ClerkUser]:
    """Same as get_current_user but returns None instead of 401."""
    if not settings.enable_clerk_auth:
        return ClerkUser(user_id="anonymous")
    if credentials is None:
        return None
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


# ── Clerk Backend API helpers ────────────────────────────────────

# Clerk user IDs look like "user_2abc123…" (alphanumeric + underscore).
_CLERK_USER_ID_RE = re.compile(r"^user_[A-Za-z0-9]{10,60}$")


def get_clerk_user_info(user_id: str) -> Optional[dict]:
    """Fetch full user info from Clerk Backend API.

    OWASP: ``user_id`` is validated against a strict regex before being
    interpolated into the request URL to prevent path-traversal / SSRF.
    """
    if not settings.clerk_secret_key:
        return None
    # OWASP A10 (SSRF): Validate user_id to prevent path injection.
    if not _CLERK_USER_ID_RE.match(user_id):
        log.warning(f"Rejected suspicious Clerk user_id: {user_id!r}")
        return None
    try:
        resp = httpx.get(
            f"https://api.clerk.com/v1/users/{user_id}",
            headers={"Authorization": f"Bearer {settings.clerk_secret_key}"},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        log.error(f"Clerk user fetch failed: {e}")
        return None
