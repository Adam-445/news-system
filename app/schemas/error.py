from pydantic import BaseModel

class ErrorResponse(BaseModel):
    error: str          # Human-readable message
    code: int           # HTTP status code
    detail: str | None  # Optional technical details