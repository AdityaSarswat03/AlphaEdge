"""
Redis caching utility (optional – gracefully degrades to in-memory dict).
"""
import json
import hashlib
from typing import Any, Optional
from alphaedge.config import settings
from alphaedge.logger import log

_memory_cache: dict = {}


def _get_redis():
    """Try to return a Redis connection; None if unavailable."""
    if not settings.enable_redis_cache:
        return None
    try:
        import redis as _redis

        client = _redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            password=settings.redis_password or None,
            decode_responses=True,
        )
        client.ping()
        return client
    except Exception:
        return None


_redis_client = _get_redis()


def _key(prefix: str, params: dict) -> str:
    raw = json.dumps(params, sort_keys=True)
    return f"alphaedge:{prefix}:{hashlib.md5(raw.encode()).hexdigest()}"


def cache_get(prefix: str, params: dict) -> Optional[Any]:
    """Fetch from cache."""
    k = _key(prefix, params)
    if _redis_client:
        val = _redis_client.get(k)
        if val:
            return json.loads(val)
    return _memory_cache.get(k)


def cache_set(prefix: str, params: dict, value: Any, ttl: int = None) -> None:
    """Store in cache."""
    k = _key(prefix, params)
    ttl = ttl or settings.cache_ttl_seconds
    serialised = json.dumps(value, default=str)
    if _redis_client:
        _redis_client.setex(k, ttl, serialised)
    else:
        _memory_cache[k] = json.loads(serialised)


def cache_clear(prefix: Optional[str] = None) -> None:
    """Flush cache (or just one prefix)."""
    global _memory_cache
    if _redis_client and prefix:
        for key in _redis_client.scan_iter(f"alphaedge:{prefix}:*"):
            _redis_client.delete(key)
    elif _redis_client:
        _redis_client.flushdb()
    else:
        if prefix:
            _memory_cache = {k: v for k, v in _memory_cache.items() if not k.startswith(f"alphaedge:{prefix}:")}
        else:
            _memory_cache.clear()
