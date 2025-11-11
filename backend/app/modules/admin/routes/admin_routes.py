from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.app.common.dependencies.auth import required_roles
from backend.app.common.exceptions.http import ConflictError, NotFoundError
from backend.app.modules.admin.models.permission import Permission
from backend.app.modules.admin.models.role import Role
from backend.app.modules.admin.schemas.permission import PermissionCreate
from backend.app.modules.admin.schemas.role import RoleUpdate
from backend.app.modules.users.models.user import User
from backend.app.modules.users.schemas.user import UserResponse
from backend.app.shared.db.database import get_db
from backend.app.shared.infrastructure.redis.client import RedisManager

router = APIRouter()


@router.put("/users/{user_id}/roles", response_model=UserResponse)
async def update_user_roles(
    user_id: UUID,
    new_role: RoleUpdate,
    current_user: User = Depends(required_roles(["admin"])),
    db: Session = Depends(get_db),
):

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFoundError(resource="user", identifier=user_id)

    role = db.query(Role).filter(Role.name == new_role.role).first()
    if not role:
        raise NotFoundError(resource="role")

    user.role_name = new_role.role
    db.commit()
    db.refresh(user)
    return user


@router.post("/roles/{role_name}/permissions")
def add_permission_to_role(
    role_name: str,
    permission_name: str,
    current_user: User = Depends(required_roles(["admin"])),
    db: Session = Depends(get_db),
):
    role = db.query(Role).filter(Role.name == role_name).first()
    permission = db.query(Permission).filter(Permission.name == permission_name).first()

    if not role or not permission:
        raise NotFoundError(resource="role or permission")

    if permission not in role.permissions:
        role.permissions.append(permission)
        db.commit()

    return {"message": "Permission added"}


@router.post("/permissions", status_code=status.HTTP_201_CREATED)
def create_permission(
    permission: PermissionCreate,
    current_user: User = Depends(required_roles(["admin"])),
    db: Session = Depends(get_db),
):
    existing = db.query(Permission).filter_by(name=permission.name).first()
    if existing:
        raise ConflictError(resource="permission")

    new_perm = Permission(**permission.model_dump())
    db.add(new_perm)
    db.commit()
    db.refresh(new_perm)
    return new_perm


@router.get("/cache-stats")
async def get_cache_stats():
    redis = await RedisManager.get_redis()
    data = {
        "total_keys": await redis.dbsize(),
        "all_keys": await redis.keys("*"),
        "article_keys": await redis.keys("cache:article:*"),
    }
    return data
