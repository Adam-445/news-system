from fastapi import status


class APIError(Exception):
    """Base class for all API errors."""

    def __init__(self, status_code: int, message: str, detail: str = None):
        self.status_code = status_code
        self.message = message
        self.detail = detail


# Specific errors
class NotFoundError(APIError):
    def __init__(self, resource: str, identifier: str | int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            message=f"{resource} not found",
            detail=f"No {resource} with ID {identifier} found",
        )


class PermissionDeniedError(APIError):
    def __init__(self, action: str = "perform this action", resource: str = None):
        detail = f"You lack permission to {action}"
        if resource:
            detail += f" on {resource}"
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            message="Permission denied",
            detail=detail,
        )


class ValidationError(APIError):
    def __init__(self, field: str, issue: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message="Validation failed",
            detail=f"Field '{field}': {issue}",
        )
