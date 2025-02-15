from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.db.database import get_db
from app import schemas
from app.api.dependencies import required_roles
from app.db import models
from app.core.errors import NotFoundError, ConflictError

router = APIRouter()


@router.put("/users/{user_id}/roles", response_model=schemas.UserResponse)
async def update_user_roles(
    user_id: UUID,
    new_role: schemas.RoleUpdate,
    current_user: models.User = Depends(required_roles(["admin"])),
    db: Session = Depends(get_db),
):

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise NotFoundError(resource="user", identifier=user_id)

    role = db.query(models.Role).filter(models.Role.name == new_role.role).first()
    if not role:
        raise NotFoundError(resource="role")

    user.role_name = new_role.role
    db.commit()
    db.refresh(user)
    return user


# @router.put("/roles/{role_name}", response_model=RoleUpdate)
# def update_role(
#     role_name: str,
#     role_update: RoleUpdate,
#     current_user: models.User = Depends(required_roles(["admin"])),
#     db: Session = Depends(get_db),
# ):
#     role = db.query(models.Role).filter(models.Role.name == role_name).first()
#     if not role:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND, detail="Role not found"
#         )
#     if role_update.description is not None:
#         role.description = role_update.description
#     db.commit()
#     db.refresh(role)
#     return role


@router.post("/roles/{role_name}/permissions")
def add_permission_to_role(
    role_name: str,
    permission_name: str,
    current_user: models.User = Depends(required_roles(["admin"])),
    db: Session = Depends(get_db),
):
    role = db.query(models.Role).filter(models.Role.name == role_name).first()
    permission = (
        db.query(models.Permission)
        .filter(models.Permission.name == permission_name)
        .first()
    )

    if not role or not permission:
        raise NotFoundError(resource="role or permission")

    if permission not in role.permissions:
        role.permissions.append(permission)
        db.commit()

    return {"message": "Permission added"}


@router.post("/permissions", status_code=status.HTTP_201_CREATED)
def create_permission(
    permission: schemas.PermissionCreate,
    current_user: models.User = Depends(required_roles(["admin"])),
    db: Session = Depends(get_db),
):
    existing = db.query(models.Permission).filter_by(name=permission.name).first()
    if existing:
        raise ConflictError(resource="permission")

    new_perm = models.Permission(**permission.model_dump())
    db.add(new_perm)
    db.commit()
    db.refresh(new_perm)
    return new_perm
