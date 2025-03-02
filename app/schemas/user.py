from datetime import datetime
from pydantic import BaseModel, EmailStr, UUID4, ConfigDict, field_validator
from typing import Optional


class UserBase(BaseModel):
    username: str
    email: EmailStr


class UserCreate(UserBase):
    password: str

    @field_validator("password")
    def validate_password(cls, v):
        if len(v) < 10:
            raise ValueError("Password must be at least 10 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain an uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain a number")
        return v
    
    model_config = ConfigDict(json_schema_extra={
        "examples": [
            {
                "email": "user@example.com",
                "username": "secure_user123",
                "password": "Str0ngP@ssw0rd!"
            }
        ]
    })


class UserResponse(UserBase):
    id: UUID4
    is_deleted: bool
    role_name: str
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "username": "johndoe",
                    "email": "johndoe@example.com",
                    "role_name": "regular",
                    "created_at": "2024-02-20T14:30:00Z",
                    "is_deleted": False,
                }
            ]
        },
    )


class UserUpdate(UserBase):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str
    role: str
    jti: Optional[str] = None
