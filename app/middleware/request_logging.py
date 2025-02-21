import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from http import HTTPStatus

from app.middleware.correlation import correlation_id

logger = logging.getLogger("app.request")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    def get_status_message(self, status_code: int) -> str:
        """Get a descriptive message for HTTP status codes"""
        try:
            return f"{HTTPStatus(status_code).phrase}: {HTTPStatus(status_code).description}"
        except ValueError:
            return "Unknown Status"

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        cid = correlation_id.get() or "none"

        # Request started
        logger.info(
            f"{request.method} request to {request.url.path}",
            extra={
                "event_type": "request_started",
                "path": request.url.path,
                "method": request.method,
                "correlation_id": cid,
                "client": request.client.host if request.client else None,
                "query_params": dict(request.query_params),
            },
        )

        try:
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
                    "correlation_id": cid,
                    "processing_time": f"{time.time() - start_time:.4f}s",
                    "response_headers": dict(response.headers),
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
                    "correlation_id": cid,
                    "processing_time": f"{time.time() - start_time:.4f}s",
                },
            )
            raise

        return response
