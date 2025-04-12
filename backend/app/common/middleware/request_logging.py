import logging
import time
from http import HTTPStatus

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from backend.app.common.middleware.correlation import correlation_id

logger = logging.getLogger("app.request")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    def get_status_message(self, status_code: int) -> str:
        """Get a descriptive message for HTTP status codes"""
        try:
            return f"{HTTPStatus(status_code).phrase}: {HTTPStatus(status_code).description}"
        except ValueError:
            return "Unknown Status"

    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/health":
            return await call_next(request)

        start_time = time.time()
        # Add critical request metadata to all logs
        record_attrs = {
            "path": request.url.path,
            "method": request.method,
            "client_ip": request.client.host if request.client else None,
            "correlation_id": correlation_id.get() or "none",
        }

        try:
            # Request started
            logger.info(
                f"{request.method} request to {request.url.path}",
                extra={"event_type": "request_started", **record_attrs},
            )
            response = await call_next(request)

            # Get readable message
            status_message = self.get_status_message(response.status_code)

            # Request Completed
            logger.info(
                f"{request.method} {request.url.path} completed: {status_message}",
                extra={
                    "event_type": "request_completed",
                    "status_code": response.status_code,
                    "status_phrase": HTTPStatus(response.status_code).phrase,
                    "processing_time": f"{time.time() - start_time:.4f}s",
                    "response_headers": dict(response.headers),
                    **record_attrs,
                },
            )

        except Exception as e:
            # Error logging
            logger.error(
                f"{request.method} {request.url.path} failed: {str(e)}",
                exc_info=True,
                extra={
                    "event_type": "request_failed",
                    "error_type": e.__class__.__name__,
                    "processing_time": f"{time.time() - start_time:.4f}s",
                    **record_attrs,
                },
            )
            raise

        return response
