from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.db.database import get_db
from app.db import models
from app.api.dependencies import required_roles, get_current_user
import app.schemas as schemas
from app.crud.users import UserService
from app.crud.preference import PreferenceService
from app.core.errors import BadRequestError

router = APIRouter()


@router.get(
    "/",
    response_model=List[schemas.UserResponse],
    summary="Retrieve all users",
    description="""
    Fetch a paginated list of users from the database.
    
    - **Admin/Moderator required.**
    - Supports sorting by fields like `created_at`.
    - Returns soft-deleted users as well.
    """,
    response_description="A list of users with profile details.",
)
def get_users(
    limit: int = Query(
        10, ge=1, le=100, description="Max number of users to retrieve."
    ),
    skip: int = Query(0, ge=0, description="Number of users to skip for pagination."),
    sort_by: str = Query("created_at", description="Sort field (e.g., `created_at`)."),
    order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order."),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return UserService.get_all_users(
        db, limit=limit, skip=skip, sort_by=sort_by, order=order
    )


@router.get(
    "/search",
    response_model=List[schemas.UserResponse],
    summary="Search users by criteria",
    description="Search users using email or username.",
)
def search_users(
    email: Optional[str] = None,
    username: Optional[str] = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Search users by email or username.
    """
    if not any([username, email]):
        raise BadRequestError(
            message="Invalid search request",
            detail="At least one search parameter must be provided",
        )
    return UserService.search_users(db, email=email, username=username)


@router.get(
    "/{id}",
    response_model=schemas.UserResponse,
    summary="Retrieve a user by ID",
    description="Fetch a single user by their unique ID.",
)
def get_user_by_id(
    id: UUID,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return UserService.get_user_by_id(db, user_id=id)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a user",
    description="""
    Soft-delete a user by marking their profile as deleted.
    
    - **Requires Admin privileges.**
    - User is not permanently removed, but marked as inactive.
    """,
    responses={
        204: {"description": "User successfully deleted."},
        403: {"description": "Forbidden – requires admin privileges."},
        404: {
            "description": "User not found.",
            "content": {
                "application/json": {
                    "example": {
                        "message": "User not found",
                        "detail": "No user found with ID 42",
                        "code": 404,
                    }
                }
            },
        },
    },
)
def delete_user(
    id: UUID,
    current_user: models.User = Depends(required_roles(["admin"])),
    db: Session = Depends(get_db),
):
    UserService.delete_user(db, id)
    return {"message": "User deleted successfully"}


@router.patch(
    "/undelete/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Undelete a user by ID",
)
def undelete_user(
    id: UUID,
    current_user: models.User = Depends(required_roles(["admin"])),
    db: Session = Depends(get_db),
):
    UserService.undelete_user(db, id)
    return {"message": "User restored successfully"}


@router.patch(
    "/{id}",
    response_model=schemas.UserResponse,
    summary="Update an existing user by ID.",
)
def update_user(
    id: UUID,
    new_user: schemas.UserUpdate,
    current_user: models.User = Depends(required_roles(["admin", "moderator"])),
    db: Session = Depends(get_db),
):
    return UserService.update_user(db, id, new_user)


@router.get(
    "/preferences",
    response_model=schemas.UserPreferenceResponse,
    summary="Get user preferences",
    description="""
    Retrieve the authenticated user's preferences.

    - **Authentication required.**
    - Users can only retrieve their own preferences.
    """,
    dependencies=[Depends(get_current_user)],
)
def get_preferences(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return PreferenceService.get_preferences(db, current_user.id)


@router.put(
    "/preferences",
    response_model=schemas.UserPreferenceResponse,
    summary="Update user preferences.",
)
def update_preferences(
    prefs: schemas.UserPreferenceUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return PreferenceService.update_preferences(db, current_user.id, prefs.model_dump())
