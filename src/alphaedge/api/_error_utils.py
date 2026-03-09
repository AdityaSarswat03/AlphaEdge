"""
Centralised error-response helper.

OWASP: Never expose raw exception messages, stack traces, or internal
file paths to external clients.  In production, return a generic message;
in development, forward the original string for debugging convenience.
"""

from alphaedge.config import settings

# Exception classes that are safe to surface verbatim (e.g. domain errors).
_SAFE_EXCEPTIONS = (ValueError, KeyError)


def safe_error_detail(exc: Exception) -> str:
    """Return a client-safe error message.

    * **development** — the original ``str(exc)`` is returned so devs get
      full context in API responses.
    * **production** — only exceptions in ``_SAFE_EXCEPTIONS`` are surfaced.
      Everything else becomes a generic message.  The *full* detail is
      always logged server-side by the caller.
    """
    if settings.app_env != "production":
        # Dev / staging: full detail is fine
        return str(exc)

    if isinstance(exc, _SAFE_EXCEPTIONS):
        return str(exc)

    return "An internal error occurred. Please try again later."
