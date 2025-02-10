from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError

from app.db import models
from app import schemas
from app.services.scraping import scrape_via_api

import logging

logger = logging.getLogger(__name__)


class ArticleService:
    @staticmethod
    def search_articles(
        db: Session, filters: schemas.ArticleFilters, skip: int = 0, limit: int = 10
    ):
        category: str = filters.category
        source: str = filters.source
        keyword: str = filters.keyword
        start_date: datetime = filters.start_date
        end_date: datetime = filters.end_date
        sort_by: str = filters.sort_by
        order: str = filters.order

        query = db.query(models.Article)

        # Apply filters
        if category:
            query = query.filter(models.Article.category.ilike(f"%{category}%"))
        if source:
            query = query.filter(models.Article.source.ilike(f"%{source}%"))
        if keyword:
            query = query.filter(
                models.Article.title.ilike(f"%{keyword}%")
                | models.Article.content.ilike(f"%{keyword}%")
            )
        if start_date and end_date:
            query = query.filter(
                models.Article.published_at.between(start_date, end_date)
            )
        elif start_date:
            query = query.filter(models.Article.published_at >= start_date)
        elif end_date:
            query = query.filter(models.Article.published_at <= end_date)

        # Sorting
        # Verify column existence
        sort_column = getattr(models.Article, sort_by, None)
        if sort_column:
            query = query.order_by(
                sort_column.desc() if order == "desc" else sort_column.asc()
            )

        articles = query.offset(skip).limit(limit).all()
        total_count = query.count()
        return articles, str(total_count)

    @staticmethod
    def create_article(db: Session, article_data: schemas.ArticleCreate):
        existing = (
            db.query(models.Article)
            .filter(models.Article.url == article_data.url)
            .first()
        )
        if existing:
            raise HTTPException(status_code=409, detail="URL exists")
        try:
            article = models.Article(**article_data.model_dump())
            db.add(article)
            db.commit()
            db.refresh(article)
            return article
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Error creating article.")

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
        # Avoid duplicates by URL
        stmt = stmt.on_conflict_do_nothing(index_elements=["url"])
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
        article = (
            db.query(models.Article).filter(models.Article.id == article_id).first()
        )
        if article:
            article.views += 1
            db.commit()
            db.refresh(article)
        return article

    @staticmethod
    def delete_article(db: Session, article_id: int) -> bool:
        article = db.query(models.Article).filter(models.Article.id == article_id)
        if not article.first():
            return False
        article.delete(synchronize_session=False)
        db.commit()
        return True

    @staticmethod
    def update_article(db: Session, article_id: int, new_data: schemas.ArticleCreate):
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
