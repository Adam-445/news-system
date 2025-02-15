from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging
import os

from app.api.v1 import articles, users, auth, admin
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.errors import APIError, ServerError
from app.middleware.correlation import CorrelationMiddleware, correlation_id
from app.middleware.request_logging import RequestLoggingMiddleware
from app.middleware.sanitization import SanitizationMiddleware

setup_logging()
logger = logging.getLogger(__name__)


app = FastAPI(
    title="News Recommendation System",
    description="API for recommending news articles using machine learning",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Log request with correlation ID
app.add_middleware(RequestLoggingMiddleware)
# Clean up sensitive data before logging
app.add_middleware(SanitizationMiddleware)
# Ensure correlation ids exist early
app.add_middleware(CorrelationMiddleware)


api_routers = [
    (auth.router, "/auth", ["Authentication"]),
    (users.router, "/users", ["Users"]),
    (articles.router, "/articles", ["Articles"]),
    (admin.router, "/admin", ["Admin Management"]),
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

# FastAPI uses reverse registration order (last registered runs first)
# We want specific handlers first, generic last


@app.exception_handler(RequestValidationError)
async def handle_validation_error(request: Request, exc: RequestValidationError):
    """Standardize validation error responses"""
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


@app.exception_handler(APIError)
async def handle_api_error(request: Request, exc: APIError):
    """Centralized error handling for all known API errors"""
    error_content = exc.to_dict()
    error_content.update(
        {"path": request.url.path, "correlation_id": correlation_id.get()}
    )
    return JSONResponse(status_code=exc.status_code, content=error_content)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Fallback for unexpected errors"""
    logger = logging.getLogger("app.error")
    logger.critical(
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

    return JSONResponse(
        status_code=server_error.status_code,
        content=server_error.to_dict()
        | {"path": request.url.path, "correlation_id": correlation_id.get()},
    )


# -------------------------------------------------------------------
# Health Check Endpoint
# -------------------------------------------------------------------
@app.get(
    "/",
    summary="API Health Check",
    response_description="System status information",
    tags=["System"],
)
async def health_check() -> dict:
    """Get API health status"""
    return {"status": "ok", "version": app.version, "environment": settings.environment}
