from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from backend.app.common.exceptions.handlers import (
    global_exception_handler,
    handle_api_error,
    handle_validation_error,
)
from backend.app.common.exceptions.http import APIError


def register_exception_handlers(app: FastAPI) -> None:
    """Wire up central exception handlers."""
    app.exception_handler(RequestValidationError)(handle_validation_error)
    app.exception_handler(APIError)(handle_api_error)
    app.exception_handler(Exception)(global_exception_handler)
