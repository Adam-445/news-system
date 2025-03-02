from typing import List

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session, joinedload

from app.core.errors import NotFoundError, PermissionDeniedError, UnauthorizedError
from app.core.security import verify_access_token
from app.db import models
from app.db.database import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> models.User:

    token_data = verify_access_token(
        token, UnauthorizedError(detail="Could not validate credentials")
    )
    # Eager load the role for quicker checks:
    user = (
        db.query(models.User)
        .options(joinedload(models.User.role).joinedload(models.Role.permissions))
        .filter(models.User.username == token_data.username)
        .first()
    )
    if not user:
        raise NotFoundError(resource="user", identifier=token_data.username)
    # Pre comput the flag
    db.info["is_admin"] = user.role.name == "admin"
    return user


def required_roles(allowed_roles: List[str]):
    def role_checker(user: models.User = Depends(get_current_user)):
        if user.role.name not in allowed_roles:
            raise PermissionDeniedError(action=f"access this endpoint")
        return user

    return role_checker


def required_permissions(required_permission: str):
    def permission_checker(user: models.User = Depends(get_current_user)):
        user_permissions = {perm.name for perm in user.role.permissions}
        if required_permission not in user_permissions:
            raise PermissionDeniedError(action=f"access this endpoint")
        return user

    return permission_checker
