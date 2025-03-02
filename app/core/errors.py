from uuid import UUID
from fastapi import status
from typing import Optional, Union, Dict, Any, List
import logging

# Configure logging for error reporting
logger = logging.getLogger(__name__)


class APIError(Exception):
    """
    Base class for API errors.
    Provides consistent error formatting, extra context, and automatic logging for server errors.
    
    Attributes:
        status_code (int): HTTP status code.
        error_code (str): Machine-readable error code.
        message (str): Human-readable error message.
        detail (Optional[str]): Detailed error explanation.
        extra (Dict[str, Any]): Additional error context.
    """
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code: str = "internal_server_error"
    message: str = "An unexpected error occurred"

    def __init__(
        self,
        message: Optional[str] = None,
        detail: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
        log_context: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.message = message if message is not None else self.__class__.message
        self.detail = detail
        self.extra = extra or {}
        self.log_context = log_context or {}
        
        # Automatically log server errors
        if 500 <= self.status_code < 600:
            logger.error(
                f"{self.__class__.__name__}: {self.message}",
                extra={
                    "status_code": self.status_code,
                    "error_code": self.error_code,
                    "detail": self.detail,
                    **self.log_context,
                },
            )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize error to a dictionary for API responses."""
        response = {
            "status": self.status_code,
            "code": self.error_code,
            "message": self.message,
            "detail": self.detail,
        }
        response.update(self.extra)
        return response

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__}(status_code={self.status_code}, "
            f"error_code='{self.error_code}', message='{self.message}', detail='{self.detail}')>"
        )

    def __str__(self) -> str:
        return f"{self.status_code} {self.error_code}: {self.message} - {self.detail}"


# ======== Client (4xx) Errors ========

class ClientError(APIError):
    """Base class for all client errors (HTTP 4xx)."""
    status_code: int = status.HTTP_400_BAD_REQUEST
    error_code: str = "client_error"
    message: str = "Invalid request"


class NotFoundError(ClientError):
    """Error raised when a requested resource is not found."""
    status_code: int = status.HTTP_404_NOT_FOUND
    error_code: str = "not_found"
    message: str = "Resource not found"

    def __init__(
        self,
        resource: str,
        identifier: Optional[Union[str, int, UUID]] = None,
        message: Optional[str] = None,
        detail: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        computed_detail = detail
        if computed_detail is None:
            computed_detail = f"{resource.capitalize()} not found"
            if identifier is not None:
                computed_detail += f" with identifier '{identifier}'"
        extra = {"resource": resource, "identifier": str(identifier) if identifier is not None else None}
        super().__init__(message=message, detail=computed_detail, extra=extra, **kwargs)


class PermissionDeniedError(ClientError):
    """Error raised when the user lacks permission to perform an action."""
    status_code: int = status.HTTP_403_FORBIDDEN
    error_code: str = "permission_denied"
    message: str = "Permission denied"

    def __init__(
        self,
        action: str = "perform this action",
        resource: Optional[str] = None,
        required_permissions: Optional[List[str]] = None,
        message: Optional[str] = None,
        detail: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        computed_detail = detail
        if computed_detail is None:
            computed_detail = f"You lack permission to {action}"
            if resource:
                computed_detail += f" on {resource}"
        extra = {"action": action, "resource": resource, "required_permissions": required_permissions or []}
        super().__init__(message=message, detail=computed_detail, extra=extra, **kwargs)


class ValidationError(ClientError):
    """Error raised when input validation fails."""
    status_code: int = status.HTTP_422_UNPROCESSABLE_ENTITY
    error_code: str = "validation_failed"
    message: str = "Validation failed"

    def __init__(
        self,
        field_errors: Optional[Dict[str, List[str]]] = None,
        message: Optional[str] = None,
        detail: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        computed_detail = detail or "Request validation failed"
        extra = {"field_errors": field_errors} if field_errors else {}
        super().__init__(message=message, detail=computed_detail, extra=extra, **kwargs)


class ConflictError(ClientError):
    """Error raised when a resource conflict occurs."""
    status_code: int = status.HTTP_409_CONFLICT
    error_code: str = "conflict"
    message: str = "Resource conflict"

    def __init__(
        self,
        resource: str,
        conflicting_field: Optional[str] = None,
        message: Optional[str] = None,
        detail: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        computed_detail = detail
        if computed_detail is None:
            computed_detail = f"{resource} already exists"
            if conflicting_field:
                computed_detail += f" (conflict on '{conflicting_field}')"
        extra = {"resource": resource, "conflicting_field": conflicting_field}
        super().__init__(message=message, detail=computed_detail, extra=extra, **kwargs)


class UnauthorizedError(ClientError):
    """Error raised when authentication fails or is missing."""
    status_code: int = status.HTTP_401_UNAUTHORIZED
    error_code: str = "unauthorized"
    message: str = "Unauthorized"

    def __init__(
        self,
        message: Optional[str] = None,
        detail: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        computed_detail = detail or "Authentication failed: invalid or missing credentials"
        extra = {"authentication": "Bearer"}
        super().__init__(message=message, detail=computed_detail, extra=extra, **kwargs)


class RateLimitError(ClientError):
    """Error raised when the request rate limit is exceeded."""
    status_code: int = status.HTTP_429_TOO_MANY_REQUESTS
    error_code: str = "rate_limit_exceeded"
    message: str = "Rate limit exceeded"

    def __init__(
        self,
        retry_after: Optional[int] = None,
        request = None,
        response = None,
        message: Optional[str] = None,
        detail: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        computed_detail = detail
        if computed_detail is None:
            computed_detail = "Too many requests"
            if retry_after:
                computed_detail += f", retry after {retry_after} seconds"
        extra = {"retry_after": retry_after}
        super().__init__(message=message, detail=computed_detail, extra=extra, **kwargs)


class BadRequestError(ClientError):
    """Error raised when a bad request is made."""
    status_code: int = status.HTTP_400_BAD_REQUEST
    error_code: str = "bad_request"
    message: str = "Bad request"

    def __init__(
        self,
        message: Optional[str] = None,
        detail: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        computed_message = message or self.__class__.message
        super().__init__(message=computed_message, detail=detail, **kwargs)


# ======== Server (5xx) Errors ========

class ServerError(APIError):
    """Base class for all server errors (HTTP 5xx)."""
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code: str = "internal_server_error"
    message: str = "Internal server error"


class DatabaseError(ServerError):
    """Error raised when a database operation fails."""
    error_code: str = "database_error"
    message: str = "Database error occurred"


class ThirdPartyServiceError(ServerError):
    """Error raised when an external service call fails."""
    error_code: str = "third_party_service_error"
    message: str = "External service error"

    def __init__(
        self,
        service_name: str,
        message: Optional[str] = None,
        detail: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        computed_detail = detail or f"Service '{service_name}' failed to respond"
        extra = {"service_name": service_name}
        super().__init__(message=message, detail=computed_detail, extra=extra, **kwargs)
