import asyncio
import logging
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from backend.app.common.config.settings import settings
from backend.app.common.exceptions.http import APIError, ServerError
from backend.app.common.logging.config import logger, setup_logging
from backend.app.common.middleware.correlation import (
    CorrelationMiddleware,
    correlation_id,
)
from backend.app.common.middleware.request_logging import RequestLoggingMiddleware
from backend.app.common.middleware.sanitization import SanitizationMiddleware
from backend.app.common.security.rate_limiting import init_limiter
from backend.app.modules.admin.routes import admin_routes
from backend.app.modules.articles.routes import article_routes
from backend.app.modules.articles.utils.view_utils.view_sync import ViewSynchronizer
from backend.app.modules.articles.utils.view_utils.view_tracker import view_tracker
from backend.app.modules.auth.routes import auth_routes
from backend.app.modules.users.routes import preference_routes, user_routes
from backend.app.shared.infrastructure.redis.client import RedisManager

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize rate limiter if not in test mode or if forced
    if settings.environment != "test" or getattr(
        app.state, "force_rate_limiter_init", False
    ):
        await init_limiter(is_test=(settings.environment == "test"), enabled=True)
        logger.info("Rate limiter initialized.")

    # Initialize services
    tracker = view_tracker
    sync = ViewSynchronizer()

    # Start background tasks
    await tracker.start_periodic_flush()
    app.state.view_syncer = asyncio.create_task(_run_sync(sync))

    try:
        redis = await RedisManager.get_redis(is_test=(settings.environment == "test"))
        logger.info("Connected to Redis.")

        logger.info("View sync task started.")
        yield
    except Exception as e:
        logger.error("Error connecting to Redis.", exc_info=e)
        raise
    finally:
        # Graceful shutdown
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
    """Separate sync loop with crash protection"""
    while True:
        try:
            await sync.sync()
            await asyncio.sleep(300)  # 5 minutes
        except Exception as e:
            logger.critical("View sync crashed", exc_info=e)
            await asyncio.sleep(60)  # Prevent tight crash loops


app = FastAPI(
    title="News Recommendation System",
    description="API for recommending news articles using machine learning",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
    # dependencies=[Depends(get_rate_limiter(times=100, hours=1))],
)

# Middleware registration order matters (reverse order of execution):
# - CorrelationMiddleware runs first (ensuring correlation ids are available)
# - SanitizationMiddleware cleans sensitive data before logging
# - RequestLoggingMiddleware logs the request
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(SanitizationMiddleware)
app.add_middleware(CorrelationMiddleware)

api_routers = [
    (auth_routes.router, "/auth", ["Authentication"]),
    (user_routes.router, "/users", ["Users"]),
    (preference_routes.router, "/preferences", ["Preferences"]),
    (article_routes.router, "/articles", ["Articles"]),
    (admin_routes.router, "/admin", ["Admin Management"]),
]

for router, prefix, tags in api_routers:
    app.include_router(
        router,
        prefix=f"/api/v1{prefix}",
        tags=tags,
        responses={
            401: {"description": "Unauthorized"},
            403: {"description": "Forbidden"},
            404: {"description": "Not Found"},
        },
    )


# Exception handler for validation errors
@app.exception_handler(RequestValidationError)
async def handle_validation_error(request: Request, exc: RequestValidationError):
    errors = [
        {
            "field": ".".join(map(str, err["loc"])),
            "message": err["msg"],
            "type": err["type"],
        }
        for err in exc.errors()
    ]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Request validation failed",
            "code": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "detail": errors,
            "path": request.url.path,
            "correlation_id": correlation_id.get(),
        },
    )


# Centralized error handling for known API errors
@app.exception_handler(APIError)
async def handle_api_error(request: Request, exc: APIError):
    error_content = exc.to_dict()
    error_content.update(
        {"path": request.url.path, "correlation_id": correlation_id.get()}
    )
    return JSONResponse(status_code=exc.status_code, content=error_content)


# Global exception handler for unexpected errors
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_logger = logging.getLogger("backend.app.error")
    error_logger.critical(
        "Unhandled exception",
        exc_info=exc,
        extra={
            "path": request.url.path,
            "method": request.method,
            "correlation_id": correlation_id.get() or "none",
        },
    )
    server_error = ServerError(
        detail="An unexpected error occurred. Please try again later."
    )
    # Explicitly merge dictionaries for clarity
    content = server_error.to_dict()
    content["path"] = request.url.path
    content["correlation_id"] = correlation_id.get()
    return JSONResponse(
        status_code=server_error.status_code,
        content=content,
    )


# -------------------------------------------------------------------
# Health Check Endpoint
# -------------------------------------------------------------------
@app.get(
    "/health",
    summary="API Health Check",
    response_description="System status information",
    tags=["System"],
)
async def health_check() -> dict:
    return {
        "status": "ok",
        "version": app.version,
        "environment": settings.environment,
    }
