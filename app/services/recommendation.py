from sqlalchemy.orm import Session

from app.crud.preference import PreferenceService
from app.db import models


def get_personalized_recommendation(db: Session, user_id: str):
    prefs = PreferenceService.get_preferences(db, user_id)
    saved_articles = prefs.saved_articles if prefs else []

    # Get categories and sources from saved articles
    # Sets for unique categories and sources
    saved_categories = set()
    saved_sources = set()

    # If there are saved articles, fetch their categories and sources
    if saved_articles:
        saved_articles_data = (
            db.query(models.Article.category, models.Article.source)
            .filter(models.Article.id.in_(saved_articles))
            .all()
        )

        saved_categories = {data[0] for data in saved_articles_data if data[0]}
        saved_sources = {data[1] for data in saved_articles_data if data[1]}

    base_query = db.query(models.Article)

    # Combine the user's preferences (if available) with the saved categories/sources
    categories = list(set(prefs.preferred_categories if prefs else []) | saved_categories)
    sources = list(set(prefs.preferred_sources if prefs else []) | saved_sources)

    if categories:
        base_query = base_query.filter(models.Article.category.in_(categories))
    if sources:
        base_query = base_query.filter(models.Article.source.in_(sources))

    # Order by popularity (views) and recency
    return base_query.order_by(
        models.Article.views.desc(), models.Article.published_at.desc()
    ).limit(20)
