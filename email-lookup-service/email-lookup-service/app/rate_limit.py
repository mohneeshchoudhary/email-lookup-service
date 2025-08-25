# app/rate_limit.py
from fastapi import HTTPException, Request
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
from .cache import get_redis
from .config import settings
import asyncio, time

_memory_lock = asyncio.Lock()
_hits: dict[str, list[float]] = {}

async def init_rate_limiter(app):
    # Use fastapi-limiter only when Redis is configured
    r = await get_redis()
    if r:
        await FastAPILimiter.init(r)
    # else: no init required (we'll use the local fallback)

def limiter_dep():
    """Return a dependency to enforce rate limits."""
    if settings.REDIS_URL:
        # Redis path -> use fastapi-limiter's RateLimiter
        return RateLimiter(times=settings.RATE_LIMIT_PER_MINUTE, seconds=60)

    # No Redis -> lightweight in-memory limiter per IP
    async def local_rate_limit(request: Request):
        now = time.time()
        window = 60
        limit = settings.RATE_LIMIT_PER_MINUTE
        ip = (request.client.host if request.client else "unknown") or "unknown"

        async with _memory_lock:
            ts = _hits.get(ip, [])
            ts = [t for t in ts if now - t < window]  # prune old hits
            if len(ts) >= limit:
                raise HTTPException(status_code=429, detail="Rate limit exceeded")
            ts.append(now)
            _hits[ip] = ts

    return local_rate_limit