from sqlalchemy.orm import Session
from app.db import models


class PreferenceService:
    @staticmethod
    def get_preferences(db: Session, user_id: str):
        return (
            db.query(models.UserPreference)
            .filter(models.UserPreference.user_id == user_id)
            .first()
        )

    @staticmethod
    def update_preferences(db: Session, user_id: str, prefs_data: dict):
        prefs = (
            db.query(models.UserPreference)
            .filter(models.UserPreference.user_id == user_id)
            .first()
        )

        if not prefs:
            prefs = models.UserPreference(user_id=user_id, **prefs_data)
            db.add(prefs)
        else:
            for field, value in prefs_data.items():
                setattr(prefs, field, value)

        db.commit()
        db.refresh(prefs)
        return prefs
