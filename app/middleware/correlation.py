import uuid
from contextvars import ContextVar
from fastapi import Request, Response

# Create a ContextVar to hold the correlation ID for the current request context
correlation_id: ContextVar[str] = ContextVar("correlation_id", default=None)

class CorrelationMiddleware:
    async def __call__(self, request: Request, call_next):
        # Check if the request already has a correlation ID
        # If not, generate a new one using uuid4
        cid = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        
        # Store the correlation ID in our ContextVar. This makes it available throughout the request lifecycle
        correlation_id.set(cid)

        # Process the request by passing it to the next component in the middleware chain
        response = await call_next(request)
        
        # Attach the correlation ID to the response headers so the client also knows it
        response.headers["X-Correlation-ID"] = cid
        return response
