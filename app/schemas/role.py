# app/schemas/role.py
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from app.schemas.permission import PermissionResponse


class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None


class RoleCreate(RoleBase):
    permissions: List[str] = []


class RoleResponse(RoleBase):
    permissions: List[PermissionResponse] = []
    model_config = ConfigDict(from_attributes=True)
