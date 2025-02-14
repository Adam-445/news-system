import time
import logging
from fastapi import Request

logger = logging.getLogger(__name__)

class RequestLoggingMiddleware:
    async def __call__(self, request: Request, call_next):
        start_time = time.time()
        
        # Log request
        logger.info(
            "Request received",
            extra={
                "path": request.url.path,
                "method": request.method,
                "query_params": dict(request.query_params),
                "client": request.client.host if request.client else None,
            }
        )

        # Process request
        response = await call_next(request)
        
        # Log response
        process_time = time.time() - start_time
        logger.info(
            "Response sent",
            extra={
                "status_code": response.status_code,
                "process_time": f"{process_time:.4f}s",
            }
        )
        
        return response