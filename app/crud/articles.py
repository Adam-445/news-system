from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError
from app.db import models
from app.schemas import ArticleCreate
from app.services.scraping import scrape_via_api

import logging

logger = logging.getLogger(__name__)


class ArticleService:
    @staticmethod
    def get_all_articles(db: Session, skip: int = 0, limit: int = 10):
        return query.offset(skip).limit(limit).all()

    @staticmethod
    def create_article(db: Session, article_data: ArticleCreate):
        try:
            with db.begin():
                article = models.Article(**article_data.model_dump())
                db.add(article)
                db.commit()
                db.refresh(article)
            return article
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail="Error creating article.")

    @staticmethod
    async def save_articles_to_db(db: Session):
        articles_data = await scrape_via_api()
        new_articles = [
            {
                "title": article.get("title", "Untitled").split("-")[
                    0
                ],  # Removes the source from title
                "content": article.get("description") or "No content available",
                "source": article.get("source", {}).get("name", "Unknown"),
                "url": article.get("url", "#"),
                "published_at": article.get("publishedAt"),
            }
            for article in articles_data
            if article.get("title") and article.get("url")
        ]

        stmt = insert(models.Article).values(new_articles)
        stmt = stmt.on_conflict_do_nothing(
            index_elements=["url"]
        )  # Avoid duplicates by URL

        try:
            db.execute(stmt)
            db.commit()
            logger.info("Successfully saved %d new articles", len(new_articles))
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Could not create article. Please try again later.",
            )

    @staticmethod
    def get_article_by_id(db: Session, article_id: int):
        return db.query(models.Article).filter(models.Article.id == article_id).first()

    @staticmethod
    def delete_article(db: Session, article_id: int) -> bool:
        article = db.query(models.Article).filter(models.Article.id == article_id)
        if not article.first():
            return False
        article.delete(synchronize_session=False)
        db.commit()
        return True

    @staticmethod
    def update_article(db: Session, article_id: int, new_data: ArticleCreate):
        article = (
            db.query(models.Article).filter(models.Article.id == article_id).first()
        )
        if not article:
            return None

        # Iterate over the fields provided in `new_data` and update the model instance
        # Only include fields that are set
        updated_fields = new_data.model_dump(exclude_unset=True)
        for field, value in updated_fields.items():
            setattr(article, field, value)

        db.commit()
        db.refresh(article)
        return article
