from redis.asyncio import Redis
from app.core.config import settings

redis_client: Redis | None = None

async def get_redis() -> Redis:
    global redis_client
    if not redis_client:
        redis_client = Redis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_connect_timeout=2,
            retry_on_timeout=True
        )
    return redis_client