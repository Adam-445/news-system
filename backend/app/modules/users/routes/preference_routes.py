from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.common.dependencies.auth import get_current_user
from backend.app.modules.users.models.user import User
from backend.app.modules.users.schemas.preference import (
    UserPreferenceResponse,
    UserPreferenceUpdate,
)
from backend.app.modules.users.services.preference_service import PreferenceService
from backend.app.shared.db.database import get_db

router = APIRouter()


@router.get(
    "/preferences",
    response_model=UserPreferenceResponse,
    summary="Get user preferences",
    description="""
    Retrieve the authenticated user's preferences.

    - **Authentication required.**
    - Users can only retrieve their own preferences.
    """,
    dependencies=[Depends(get_current_user)],
)
def get_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return PreferenceService.get_preferences(db, current_user.id)


@router.put(
    "/preferences",
    response_model=UserPreferenceResponse,
    summary="Update user preferences.",
)
def update_preferences(
    prefs: UserPreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return PreferenceService.update_preferences(db, current_user.id, prefs.model_dump())
