from typing import List, Optional
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.db.database import get_db
from app.db import models
from app.api.dependencies import required_roles, get_current_user
import app.schemas as schemas
from app.crud.users import UserService
from app.crud.preference import PreferenceService

router = APIRouter()


@router.get("/", response_model=List[schemas.UserResponse])
def get_users(
    limit: int = 10,
    skip: int = 0,
    sort_by: str = "created_at",
    order: str = "desc",
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Fetch all users from the database.
    """
    return UserService.get_all_users(db)


@router.get("/search", response_model=List[schemas.UserResponse])
def search_users(
    id: Optional[UUID] = None,
    email: Optional[str] = None,
    username: Optional[str] = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Search users by ID, email or username.
    """
    if not any([id, username, email]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one search parameter must be provided",
        )
    return UserService.search_users(db, id=id, email=email, username=username)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    id: UUID,
    current_user: models.User = Depends(required_roles(["admin"])),
    db: Session = Depends(get_db),
):
    """
    Delete a user by ID.
    """
    if not UserService.delete_user(db, id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {id} was not found.",
        )


@router.patch("/undelete/{id}", status_code=status.HTTP_204_NO_CONTENT)
def undelete_user(
    id: UUID,
    current_user: models.User = Depends(required_roles(["admin"])),
    db: Session = Depends(get_db),
):
    """
    Undelete a user by ID.
    """
    if not UserService.undelete_user(db, id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {id} was not found.",
        )


@router.patch("/{id}", response_model=schemas.UserResponse)
def update_user(
    id: UUID,
    new_user: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(required_roles(["admin", "moderator"])),
):
    """
    Update an existing user by ID.
    """
    updated_user = UserService.update_user(db, id, new_user)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {id} was not found.",
        )
    return updated_user


@router.get("/preferences", response_model=schemas.UserPreferenceResponse)
def get_preferences(
    user: models.User = Depends(get_current_user),
    current_user: models.User = Depends(required_roles(["admin", "moderator"])),
    db: Session = Depends(get_db),
):
    return PreferenceService.get_preferences(db, user.id)


@router.patch("/preferences")
def update_preferences(
    prefs: schemas.UserPreferenceUpdate,
    current_user: models.User = Depends(required_roles(["admin", "moderator"])),
    db: Session = Depends(get_db),
):
    return PreferenceService.update_preferences(db, prefs.user_id, prefs.model_dump())
