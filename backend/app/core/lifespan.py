import asyncio
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI

from backend.app.common.config.settings import settings
from backend.app.common.logging.config import logger
from backend.app.common.security.rate_limiting import init_limiter
from backend.app.modules.articles.utils.view_utils.view_sync import ViewSynchronizer
from backend.app.modules.articles.utils.view_utils.view_tracker import view_tracker
from backend.app.shared.infrastructure.redis.client import RedisManager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context.

    Responsible for initializing:
      - Rate limiter (unless in test unless forced)
      - View tracking periodic flush
      - Background sync task
      - Redis connection

    Ensures graceful shutdown and task cancellation.
    """
    if settings.environment != "test" or getattr(
        app.state, "force_rate_limiter_init", False
    ):
        await init_limiter(is_test=(settings.environment == "test"), enabled=True)
        logger.info("Rate limiter initialized.")

    tracker = view_tracker
    sync = ViewSynchronizer()

    # Start periodic flush task
    await tracker.start_periodic_flush()
    app.state.view_syncer = asyncio.create_task(_run_sync(sync))

    try:
        await RedisManager.get_redis(is_test=(settings.environment == "test"))
        logger.info("Connected to Redis.")
        logger.info("View sync task started.")
        yield
    except Exception as e:
        logger.error("Error during lifespan startup.", exc_info=e)
        raise
    finally:
        await tracker.stop_periodic_flush()
        app.state.view_syncer.cancel()
        with suppress(asyncio.CancelledError):
            await app.state.view_syncer
        try:
            await RedisManager.close_redis()
            logger.info("Redis connection closed.")
        except Exception as e:
            logger.error("Error closing Redis connection.", exc_info=e)


async def _run_sync(sync: ViewSynchronizer):
    """Runs the view synchronization loop with crash protection."""
    while True:
        try:
            await sync.sync()
            await asyncio.sleep(300)  # 5 minutes
        except Exception as e:
            logger.critical("View sync crashed", exc_info=e)
            await asyncio.sleep(60)  # Backoff to avoid tight crash loops
