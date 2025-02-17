from uuid import UUID
from fastapi import status
from typing import Optional, Union


class APIError(Exception):
    """
    Base class for all API errors.

    Attributes:
        status_code (int): HTTP status code.
        message (str): A short error message.
        detail (Optional[str]): A more detailed error message.
    """

    def __init__(
        self, status_code: int, message: str, detail: Optional[str] = None
    ) -> None:
        self.status_code = status_code
        self.message = message
        self.detail = detail

    def to_dict(self) -> dict:
        """
        Convert the error details to a dictionary for API responses.
        """
        return {
            "error": self.message,
            "detail": self.detail,
            "code": self.status_code,
        }

    def __str__(self) -> str:
        return f"{self.status_code} - {self.message}: {self.detail}"


class NotFoundError(APIError):
    """
    Raised when a requested resource is not found.
    """

    def __init__(
        self, resource: str, identifier: Optional[Union[str, int, UUID]] = None
    ) -> None:
        detail = f"No {resource.lower()} found"
        if identifier:
            detail += f" with ID {identifier}"
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            message=f"{resource.capitalize()} not found",
            detail=detail,
        )


class PermissionDeniedError(APIError):
    """
    Raised when the user lacks permission to perform an action.
    """

    def __init__(
        self, action: str = "perform this action", resource: Optional[str] = None
    ) -> None:
        detail = f"You lack permission to {action}"
        if resource:
            detail += f" on {resource.lower()}"
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            message="Permission denied",
            detail=detail,
        )


class ValidationError(APIError):
    """
    Raised when input validation fails.
    """

    def __init__(self, field: str, issue: str) -> None:
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message="Validation failed",
            detail=f"Field '{field}': {issue}",
        )


class ConflictError(APIError):
    """
    Raised when a resource conflict occurs.
    """

    def __init__(self, resource: str) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            message=f"{resource.capitalize()} conflict",
            detail=f"{resource.capitalize()} already exists or has conflicting data",
        )


class BadRequestError(APIError):
    """
    Raised when a bad request is made.
    """

    def __init__(self, message: str, detail: Optional[str] = None) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=message,
            detail=detail,
        )


class UnauthorizedError(APIError):
    """
    Raised when authentication is required or fails.
    """

    def __init__(
        self,
        message: str = "Authentication failed",
        detail: Optional[str] = "Invalid or missing authentication credentials",
    ) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message=message,
            detail=detail,
        )


class ServerError(APIError):
    """
    Raised for internal server errors.
    """

    def __init__(
        self,
        message: str = "An unexpected error occurred.",
        detail: Optional[str] = None,
    ) -> None:
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=message,
            detail=detail,
        )
