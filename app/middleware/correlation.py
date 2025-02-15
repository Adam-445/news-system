from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
import uuid
from contextvars import ContextVar

correlation_id: ContextVar[str] = ContextVar("correlation_id", default=None)

class CorrelationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Get or generate correlation ID
        cid = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        correlation_id.set(cid)
        
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = cid
        return response