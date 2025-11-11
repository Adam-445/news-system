from typing import List

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session, joinedload

from backend.app.common.exceptions.http import (
    NotFoundError,
    PermissionDeniedError,
    UnauthorizedError,
)
from backend.app.common.security.auth import verify_access_token
from backend.app.modules.users.models.user import User
from backend.app.shared.db.database import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:

    token_data = verify_access_token(
        token, UnauthorizedError(detail="Could not validate credentials")
    )
    # Eager load the role for quicker checks:
    user = (
        db.query(User)
        .options(joinedload(User.role))
        # .options(joinedload(User.role).joinedload(Role.permissions))
        .filter(User.username == token_data.username)
        .first()
    )
    if not user:
        raise NotFoundError(resource="user", identifier=token_data.username)
    # Pre comput the flag
    db.info["is_admin"] = user.role.name == "admin"
    return user


def required_roles(allowed_roles: List[str]):
    def role_checker(user: User = Depends(get_current_user)):
        if user.role.name not in allowed_roles:
            raise PermissionDeniedError(action=f"access this endpoint")
        return user

    return role_checker


# def required_roles(allowed_roles: List[str]):
#     def dependency(
#         current_user: User = Depends(get_current_user),  # Explicit auth first
#         db: Session = Depends(get_db)
#     ):
#         if current_user.role.name not in allowed_roles:
#             raise PermissionDeniedError(action=f"access this endpoint")
#         return current_user

#     return dependency


def required_permissions(required_permission: str):
    def permission_checker(user: User = Depends(get_current_user)):
        user_permissions = {perm.name for perm in user.role.permissions}
        if required_permission not in user_permissions:
            raise PermissionDeniedError(action=f"access this endpoint")
        return user

    return permission_checker
