from sqlalchemy.orm import Session

from app.crud.preference import PreferenceService
from app.db import models


def get_personalized_recommendation(db: Session, user_id: str):
    prefs = PreferenceService.get_preferences(db, user_id)

    base_query = db.query(models.Article)

    if prefs and prefs.preferred_categories:
        base_query = base_query.filter(
            models.Article.category.in_(prefs.preferred_categories)
        )

    if prefs and prefs.preferred_sources:
        base_query = base_query.filter(
            models.Article.source.in_(prefs.preferred_sources)
        )

    return base_query.order_by(models.Article.published_at.desc()).limit(10)
