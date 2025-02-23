from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
import json

SENSITIVE_KEYS = {"password", "token", "authorization",  "api_key", "secret", "credit_card"}


def sanitize(data):
    """Recursively sanitize sensitive keys in JSON data."""
    if isinstance(data, dict):
        new_data = {}
        for key, value in data.items():
            if key in SENSITIVE_KEYS:
                new_data[key] = "***REDACTED***"
            else:
                new_data[key] = sanitize(value)
        return new_data
    elif isinstance(data, list):
        return [sanitize(item) for item in data]
    else:
        return data


class SanitizationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Redact headers (Note: request.headers is immutable,
        # so you might log redacted values or store them in request.state)
        redacted_headers = {
            key: ("***REDACTED***" if key.lower() in SENSITIVE_KEYS else value)
            for key, value in request.headers.items()
        }
        # Save redacted headers to request.state for logging later
        request.state.redacted_headers = redacted_headers

        # Try to sanitize JSON body for logging purposes.
        try:
            body = await request.body()
            if body:
                body_json = json.loads(body)
                sanitized_body = sanitize(body_json)  # Recursively sanitize payload.
                request.state.sanitized_body = json.dumps(sanitized_body)
        except Exception:
            request.state.sanitized_body = None

        response = await call_next(request)
        return response
