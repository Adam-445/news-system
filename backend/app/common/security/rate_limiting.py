from typing import Optional

from fastapi import Request, Response
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
from redis import Redis

from backend.app.common.exceptions.http import RateLimitError
from backend.app.shared.infrastructure.redis.client import RedisManager


async def init_limiter(
    redis_client: Optional[Redis] = None, is_test: bool = False, enabled: bool = True
):
    """
    Initializes the FastAPI rate limiter using Redis.

    Args:
        is_test (bool): If True, uses the test Redis database.
        enabled (bool): If False, rate limiting is disabled.
    """
    if not enabled:
        # Skip initialization if rate limiting is disabled
        return

    try:
        # Get Redis connection (test or production)
        redis_conn = redis_client or await RedisManager.get_redis(is_test=is_test)

        await FastAPILimiter.init(redis_conn, identifier=get_identifier)
    except Exception as e:
        raise RuntimeError(f"Rate limiter initialization failed: {str(e)}") from e


async def get_identifier(request: Request) -> str:
    """
    Generates a unique identifier for rate limiting based on user ID (if available) or IP.

    Returns:
        str: Unique identifier string in the format:
             - "user:{user_id}" if authenticated user is available
             - "ip:{client_ip}:{user_agent}" if no user ID is found
    """
    # Retrieve client IP (considering proxy headers)
    forwarded = request.headers.get("X-Forwarded-For")
    client_ip = forwarded.split(",")[0] if forwarded else request.client.host

    # Include User-Agent to distinguish between different clients behind the same IP
    user_agent = request.headers.get("User-Agent", "")

    # Attempt to retrieve user ID from request state (if set by authentication middleware)
    user_id = getattr(request.state, "user_id", None)

    return f"user:{user_id}" if user_id else f"ip:{client_ip}:{user_agent}"


def rate_limiter(times: int, seconds: int):
    """
    Returns a FastAPI dependency for rate limiting API endpoints.

    Args:
        times (int): Maximum number of requests allowed within the time window.
        seconds (int): Time window in seconds for rate limiting.

    Returns:
        RateLimiter: A dependency that enforces the rate limit on an endpoint.
    """
    return RateLimiter(times=times, seconds=seconds, callback=rate_limit_callback)


async def rate_limit_callback(request: Request, response: Response, pexpire: int):
    """
    Handles requests that exceed the rate limit by raising a RateLimitError.

    Args:
        request (Request): The request that exceeded the rate limit.
        response (Response): The HTTP response object.
        pexpire (int): Remaining milliseconds until the rate limit resets.

    Raises:
        RateLimitError: Custom exception indicating rate limit violation.
    """
    raise RateLimitError(retry_after=pexpire, request=request, response=response)
