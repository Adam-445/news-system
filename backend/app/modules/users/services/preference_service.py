from sqlalchemy.orm import Session

from backend.app.modules.users.models.preference import UserPreference


class PreferenceService:
    @staticmethod
    def get_preferences(db: Session, user_id: str):
        return (
            db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
        )

    @staticmethod
    def update_preferences(db: Session, user_id: str, prefs_data: dict):
        prefs = (
            db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
        )

        if not prefs:
            prefs = UserPreference(user_id=user_id, **prefs_data)
            db.add(prefs)
        else:
            for field, value in prefs_data.items():
                setattr(prefs, field, value)

        db.commit()
        db.refresh(prefs)
        return prefs
