from fastapi import FastAPI

from backend.app.common.middleware.correlation import CorrelationMiddleware
from backend.app.common.middleware.request_logging import RequestLoggingMiddleware
from backend.app.common.middleware.sanitization import SanitizationMiddleware


def register_middleware(app: FastAPI) -> None:
    """Register middleware in correct order.

    Order matters: first added is outermost -> executes first on request.
    We want correlation early so every subsequent log has the ID.
    """
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(SanitizationMiddleware)
    app.add_middleware(CorrelationMiddleware)
