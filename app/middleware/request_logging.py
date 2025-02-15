import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.middleware.correlation import correlation_id

logger = logging.getLogger("app.request")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        # Get correlation id from the context variable
        cid = correlation_id.get() or "none"

        logger.info(
            "Request started",
            extra={
                "path": request.url.path,
                "method": request.method,
                "correlation_id": cid,
                "client": request.client.host if request.client else None,
                "query_params": dict(request.query_params),
            },
        )

        try:
            response = await call_next(request)
        except Exception as e:
            logger.error(
                "Request failed",
                exc_info=True,
                extra={
                    "correlation_id": cid,
                    "processing_time": time.time() - start_time,
                },
            )
            raise

        logger.info(
            "Request completed",
            extra={
                "status_code": response.status_code,
                "correlation_id": cid,
                "processing_time": f"{time.time() - start_time:.4f}s",
                "headers": dict(response.headers),
            },
        )

        return response
