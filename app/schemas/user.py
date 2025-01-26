from datetime import datetime
from pydantic import BaseModel, EmailStr, UUID4
from typing import Optional

class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: UUID4
    created_at: datetime

    class Config:
        from_attributes = True

class UserUpdate(UserBase):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None