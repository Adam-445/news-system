import pytest
from uuid import uuid4
from fastapi import status
from app.core.errors import (
    NotFoundError,
    ValidationError,
    PermissionDeniedError,
    UnauthorizedError,
    ConflictError,
    RateLimitError,
    ThirdPartyServiceError,
    DatabaseError,
    BadRequestError,
)

def test_not_found_error():
    error = NotFoundError(resource="User", identifier=uuid4())
    response = error.to_dict()
    assert response["status"] == status.HTTP_404_NOT_FOUND
    assert response["code"] == "not_found"
    assert "User not found" in response["detail"]

def test_validation_error():
    field_errors = {"email": ["Invalid email format"], "password": ["Too short"]}
    error = ValidationError(field_errors=field_errors)
    response = error.to_dict()
    assert response["status"] == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response["code"] == "validation_failed"
    assert response["field_errors"] == field_errors

def test_permission_denied_error():
    error = PermissionDeniedError(action="delete", resource="Article")
    response = error.to_dict()
    assert response["status"] == status.HTTP_403_FORBIDDEN
    assert response["code"] == "permission_denied"
    assert "delete" in response["detail"]
    assert "Article" in response["detail"]

def test_unauthorized_error():
    error = UnauthorizedError()
    response = error.to_dict()
    assert response["status"] == status.HTTP_401_UNAUTHORIZED
    assert response["code"] == "unauthorized"
    assert "Authentication failed" in response["detail"]

def test_conflict_error():
    error = ConflictError(resource="User", conflicting_field="email")
    response = error.to_dict()
    assert response["status"] == status.HTTP_409_CONFLICT
    assert response["code"] == "conflict"
    assert "User already exists" in response["detail"]
    assert response["conflicting_field"] == "email"

def test_rate_limit_error():
    error = RateLimitError(retry_after=30)
    response = error.to_dict()
    assert response["status"] == status.HTTP_429_TOO_MANY_REQUESTS
    assert response["code"] == "rate_limit_exceeded"
    assert "Too many requests" in response["detail"]
    assert response["retry_after"] == 30

def test_database_error():
    error = DatabaseError()
    response = error.to_dict()
    assert response["status"] == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response["code"] == "database_error"
    assert "Database error occurred" in response["message"]

def test_third_party_service_error():
    error = ThirdPartyServiceError(service_name="PaymentGateway")
    response = error.to_dict()
    assert response["status"] == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response["code"] == "third_party_service_error"
    assert "'PaymentGateway' failed to respond" in response["detail"]

def test_bad_request_error():
    error = BadRequestError(detail="Invalid query parameter")
    response = error.to_dict()
    assert response["status"] == status.HTTP_400_BAD_REQUEST
    assert response["code"] == "bad_request"
    assert response["detail"] == "Invalid query parameter"