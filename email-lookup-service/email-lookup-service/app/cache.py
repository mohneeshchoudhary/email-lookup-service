from typing import Optional
from .config import settings
import asyncio
import time

_redis = None
_memory_cache: dict[str, tuple[float, str]] = {}
_memory_lock = asyncio.Lock()

async def get_redis():
    global _redis
    if _redis is not None:
        return _redis
    if settings.REDIS_URL:
        import redis.asyncio as redis
        _redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis

async def cache_get(key: str) -> Optional[str]:
    r = await get_redis()
    if r:
        return await r.get(key)
    async with _memory_lock:
        item = _memory_cache.get(key)
        if not item:
            return None
        expiry, value = item
        if time.time() > expiry:
            _memory_cache.pop(key, None)
            return None
        return value

async def cache_set(key: str, value: str, ttl: int):
    r = await get_redis()
    if r:
        await r.setex(key, ttl, value)
        return
    async with _memory_lock:
        _memory_cache[key] = (time.time() + ttl, value)
