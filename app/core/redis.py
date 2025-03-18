import asyncio
from datetime import datetime, timezone
from typing import Optional

import jwt
import orjson
from redis.asyncio import Redis

from app.core.config import settings


class RedisManager:
    """Manages separate Redis connections for different environments (production & testing)."""

    _connections: dict[str, Optional[Redis]] = {}

    @classmethod
    async def get_redis(cls, is_test: bool = False) -> Redis:
        """Retrieve or create a Redis connection for the specified environment."""
        environment = "test" if is_test else "prod"

        if not cls._connections.get(environment):
            redis_url = (
                f"{settings.redis_url}/1" if is_test else f"{settings.redis_url}/0"
            )
            try:
                cls._connections[environment] = Redis.from_url(
                    redis_url,
                    decode_responses=True,
                    socket_connect_timeout=2,
                    retry_on_timeout=True,
                )
            except Exception as e:
                raise ConnectionError(
                    f"Failed to connect to Redis ({environment}): {e}"
                )

        return cls._connections[environment]

    @classmethod
    async def close_redis(cls):
        """Gracefully close all Redis connections on shutdown."""
        for key, conn in cls._connections.items():
            if conn:
                await conn.aclose()
                cls._connections[key] = None  # Ensures safe reinitialization later

    @classmethod
    async def cache_response(cls, key: str, data: dict, expire: int = 300):
        redis = await cls.get_redis()
        await redis.setex(
            f"cache:{key}",
            expire,
            orjson.dumps(data, option=orjson.OPT_SERIALIZE_DATACLASS),
        )

    @classmethod
    async def get_cached_response(cls, key: str):
        redis = await cls.get_redis()
        data = await redis.get(f"cache:{key}")
        if data:
            # Auto-refresh cache if < 5min left
            ttl = await redis.ttl(f"cache:{key}")
            if ttl < 300:
                await redis.expire(f"cache:{key}", 600)  # Reset TTL
            return orjson.loads(data)

        return None

    @classmethod
    async def delete_cache(cls, pattern: str):
        """Safely delete keys with matching pattern using redis.scan"""
        redis = await cls.get_redis()
        cursor = '0'
        deleted_count = 0

        # redis.scan instead of redis.keys to avoid blocking redis
        while cursor != 0:
            cursor, keys = await redis.scan(cursor=cursor, match=f"cache:{pattern}")
        
        if keys:
            # Use redis.unlink instead of redis.delete to avoid blocking using lazy deletetion
            await redis.unlink(*keys)
            deleted_count = len(keys)

        return deleted_count
    
    @classmethod
    async def increment_counter(cls, key: str, amount: int = 1):
        """Increment a counter in Redis asynchronously."""
        redis = await cls.get_redis()
        return await redis.incrby(key, amount)
    
    @classmethod
    async def get_counter(cls, key:str) -> int:
        """Get a counter value from Redis."""
        redis = await cls.get_redis()
        value = await redis.get(key)
        return int(value) if value else 0
    
    @classmethod
    async def add_to_blacklist(cls, jti: str, token: str, is_test: bool = False):
        """Adds a JWT to the Redis blacklist with an expiration time."""
        expire_seconds = cls.get_token_expiration(token)
        if expire_seconds > 0:
            conn = await cls.get_redis(is_test)
            await conn.setex(f"blacklist:{jti}", expire_seconds, "true")

    @classmethod
    async def is_token_blacklisted(cls, jti: str, is_test: bool = False) -> bool:
        """Checks if a JWT is blacklisted in Redis."""
        conn = await cls.get_redis(is_test)
        return await conn.exists(f"blacklist:{jti}") > 0

    @staticmethod
    def get_token_expiration(token: str) -> int:
        """Extracts the expiration time from a JWT and returns remaining seconds."""
        try:
            payload = jwt.decode(
                token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
            )
            exp_timestamp = payload.get("exp", 0)
            return max(0, int(exp_timestamp - datetime.now(timezone.utc).timestamp()))
        except jwt.ExpiredSignatureError:
            # Token already expired
            return 0
        except jwt.InvalidTokenError:
            # Invalid token should be considered expired
            return 0
