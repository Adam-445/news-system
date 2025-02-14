import json
import re
from fastapi import Request

SENSITIVE_KEYS = ["password", "token", "authorization"]

class SanitizationMiddleware:
    async def __call__(self, request: Request, call_next):
        headers = dict(request.headers)
        for key in SENSITIVE_KEYS:
            if key in headers:
                headers[key] = "***REDACTED***"
        request.headers = headers

        # Redact request body
        try:
            body_json = await request.json()
            for key in SENSITIVE_KEYS:
                if key in body_json:
                    body_json[key] = "***REDACTED***"
            request._body = json.dumps(body_json).encode()
        except:
            pass
        
        return await call_next(request)