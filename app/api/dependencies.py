from typing import List
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session, joinedload

from app.db import models
from app.db.database import get_db
from app.core.security import verify_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token_data = verify_access_token(token, credentials_exception)
    print(token_data.username)
    print(db.query(models.User).filter(models.User.username == token_data.username))
    # Eager load the role for quicker checks:
    user = (
        db.query(models.User)
        .options(joinedload(models.User.role).joinedload(models.Role.permissions))
        .filter(models.User.username == token_data.username)
        .first()
    )
    if not user:
        raise credentials_exception
    return user


def required_roles(allowed_roles: List[str]):
    def role_checker(user: models.User = Depends(get_current_user)):
        # Compare the user's role name with allowed roles.
        if user.role.name not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions: role not allowed",
            )
        return user

    return role_checker


def required_permissions(required_permission: str):
    def permission_checker(user: models.User = Depends(get_current_user)):
        # Assuming user.role.permissions is a list of Permission objects
        user_permissions = {perm.name for perm in user.role.permissions}
        if required_permission not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return user

    return permission_checker
