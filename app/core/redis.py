from datetime import datetime, timezone
import jwt
from redis.asyncio import Redis
from typing import Optional

from app.core.config import settings


class RedisManager:
    """Manages separate Redis connections for different environments (production & testing)."""

    _connections: dict[str, Optional[Redis]] = {}

    @classmethod
    async def get_redis(cls, is_test: bool = False) -> Redis:
        """Retrieve or create a Redis connection for the specified environment."""
        environment = "test" if is_test else "prod"

        if cls._connections.get(environment) is None:
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
