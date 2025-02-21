from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
from app.core.redis import get_redis

# Initialize Redis connection
async def init_rate_limiter():
    redis = await get_redis()
    await FastAPILimiter.init(redis)

# Rate limiter dependencies
basic_rate_limiter = RateLimiter(times=100, hours=1)
strict_rate_limiter = RateLimiter(times=5, minutes=1)