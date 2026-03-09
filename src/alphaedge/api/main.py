"""
FastAPI Application – entrypoint.

Security notes:
  - Swagger/ReDoc disabled in production (``docs_url=None``).
  - CORS restricted to explicit methods & headers (OWASP).
  - Root endpoint reveals no infrastructure details in production.
  - Health endpoint omits internal service names in production.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from alphaedge.config import settings
from alphaedge.logger import log
from alphaedge.api.routes import predictions, backtesting, analytics
from alphaedge.api.middleware import (
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
    RequestIDMiddleware,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    log.info("AlphaEdge API starting …")
    log.info(f"Environment: {settings.app_env}")
    log.info(f"Auth: {'Clerk' if settings.enable_clerk_auth else 'disabled'}")
    log.info(f"DB: Firebase (project={settings.firebase_project_id or 'not configured'})")
    log.info(f"DNS: Cloudflare ({settings.domain_name})")
    log.info(f"Rate limit: {settings.rate_limit_per_minute} req/min")
    yield
    log.info("AlphaEdge API shutting down …")


app = FastAPI(
    title="AlphaEdge API",
    description="Advanced Stock Market Prediction Platform – REST API",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,  # hide Swagger in production
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
)

# ── Middleware (order matters: outermost first) ──────────────────

# Request ID tracing
app.add_middleware(RequestIDMiddleware)

# Security headers
app.add_middleware(SecurityHeadersMiddleware)

# Rate limiting (IP + user-based; authenticated users get 3× the limit)
app.add_middleware(
    RateLimitMiddleware,
    max_requests=settings.rate_limit_per_minute,
    window_seconds=60,
    auth_multiplier=3.0,
)

# CORS — OWASP: restrict to the exact methods & headers the frontend needs.
# Wildcard "*" allows any header/method which weakens the same-origin policy.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "Accept",
        "X-Request-ID",
    ],
    expose_headers=[
        "X-Request-ID",
        "X-RateLimit-Limit",
        "X-RateLimit-Remaining",
        "X-RateLimit-Reset",
    ],
)

# Trusted hosts in production
if settings.app_env == "production" and settings.trusted_hosts:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.trusted_hosts,
    )

# Routers
app.include_router(predictions.router, prefix="/api/v1", tags=["Predictions"])
app.include_router(backtesting.router, prefix="/api/v1", tags=["Backtesting"])
app.include_router(analytics.router,   prefix="/api/v1", tags=["Analytics"])


@app.get("/", tags=["Root"])
async def root():
    # OWASP: Do not disclose infrastructure details in production.
    if settings.app_env == "production":
        return {
            "message": "AlphaEdge API",
            "version": "1.0.0",
            "status": "running",
        }
    return {
        "message": "Welcome to AlphaEdge API",
        "version": "1.0.0",
        "docs": "/docs" if settings.debug else "disabled",
        "auth": "Clerk" if settings.enable_clerk_auth else "disabled",
    }


@app.get("/health", tags=["Root"])
async def health():
    from alphaedge.utils.firebase_db import check_connection as fb_check
    firebase_ok = fb_check()

    # OWASP: Don't expose internal service topology in production.
    if settings.app_env == "production":
        return {
            "status": "healthy" if firebase_ok else "degraded",
            "version": "1.0.0",
        }
    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": settings.app_env,
        "firebase": "connected" if firebase_ok else "unavailable",
        "auth": "clerk" if settings.enable_clerk_auth else "disabled",
    }


# Allow `python -m alphaedge.api.main`
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "alphaedge.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
    )
