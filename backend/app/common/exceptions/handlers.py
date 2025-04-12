import logging

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from backend.app.common.exceptions.http import APIError, ServerError
from backend.app.common.middleware.correlation import correlation_id


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


async def handle_api_error(request: Request, exc: APIError):
    error_content = exc.to_dict()
    error_content.update(
        {"path": request.url.path, "correlation_id": correlation_id.get()}
    )
    return JSONResponse(status_code=exc.status_code, content=error_content)


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
