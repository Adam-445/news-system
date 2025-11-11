import json
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient


from backend.app.middleware.sanitization import SanitizationMiddleware

# We create a separate FastAPI test app here because middleware stores
# sanitized data in `request.state`, which is not directly accessible
# in regular tests using the `client` fixture.
# This test app allows us to inspect middleware behavior in isolation
# without relying on the full application setup.
app = FastAPI()


backend.app.add_middleware(SanitizationMiddleware)


# Create a test endpoint that returns the sanitized data stored in request.state
@backend.app.post("/test/sanitization")
async def get_sanitization_info(request: Request):
    return {
        "redacted_headers": getattr(request.state, "redacted_headers", {}),
        "sanitized_body": getattr(request.state, "sanitized_body", None),
    }


client = TestClient(app)


def test_sanitization_headers():
    """
    Test that the middleware redacts sensitive headers.
    """
    headers = {
        "Authorization": "Bearer secret_token",
        "Token": "some_token",
        "X-Custom": "value",
    }
    response = client.post("/test/sanitization", headers=headers)
    data = response.json()
    redacted = data.get("redacted_headers", {})

    # Keys in the middleware are checked in lowercase.
    assert redacted.get("authorization") == "***REDACTED***"
    assert redacted.get("token") == "***REDACTED***"
    assert redacted.get("x-custom") == "value"


def test_sanitization_body():
    """
    Test that the middleware redacts sensitive fields in a JSON body.
    """
    # Non-sensitive header for control
    headers = {"X-Custom": "value"}
    payload = {"username": "user1", "password": "mysecret", "email": "user@example.com"}

    response = client.post("/test/sanitization", headers=headers, json=payload)
    data = response.json()
    sanitized_body = data.get("sanitized_body")

    # Ensure we got back a sanitized body string.
    assert sanitized_body is not None

    # Load the JSON to verify contents.
    body_data = json.loads(sanitized_body)
    # Sensitive field should be redacted.
    assert body_data.get("password") == "***REDACTED***"
    # Other fields should remain unchanged.
    assert body_data.get("username") == "user1"
    assert body_data.get("email") == "user@example.com"


def test_sanitization_nested_objects():
    """Test redaction in nested JSON structures"""
    payload = {
        "user": {"password": "secret", "details": {"token": "nested_token"}},
        "auth": {"authorization": "Bearer abc123"},
    }

    response = client.post("/test/sanitization", json=payload)
    sanitized = json.loads(response.json()["sanitized_body"])

    assert sanitized["user"]["password"] == "***REDACTED***"
    assert sanitized["user"]["details"]["token"] == "***REDACTED***"
    assert sanitized["auth"]["authorization"] == "***REDACTED***"


def test_sanitization_non_json_body():
    """Test middleware handles non-JSON bodies gracefully"""
    response = client.post("/test/sanitization", content=b"raw binary data")
    assert response.json()["sanitized_body"] is None


def test_correlation_id_propagation(client):
    response = client.get("/api/v1/articles/")
    assert "X-Correlation-ID" in response.headers
    assert len(response.headers["X-Correlation-ID"]) == 36
