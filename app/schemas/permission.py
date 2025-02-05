from typing import Optional
from pydantic import BaseModel, ConfigDict

class PermissionBase(BaseModel):
    name: str
    description: Optional[str] = None

class PermissionCreate(PermissionBase):
    pass

class PermissionResponse(PermissionBase):
    model_config = ConfigDict(from_attributes=True)
