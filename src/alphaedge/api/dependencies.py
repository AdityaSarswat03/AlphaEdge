"""
Shared FastAPI dependencies (predictor singleton + Clerk auth).
"""

from functools import lru_cache
from alphaedge.core.predictor import AlphaEdge
from alphaedge.auth import get_current_user, get_optional_user, ClerkUser  # noqa: F401


@lru_cache(maxsize=1)
def get_predictor() -> AlphaEdge:
    """Return a single shared AlphaEdge predictor instance."""
    return AlphaEdge()
