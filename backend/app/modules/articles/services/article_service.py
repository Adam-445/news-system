from datetime import datetime, timezone
from uuid import UUID

from pydantic import ValidationError
from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.app.common.exceptions.http import (
    BadRequestError,
    ConflictError,
    NotFoundError,
    ServerError,
)
from backend.app.common.logging.config import logger
from backend.app.modules.articles.models.article import Article
from backend.app.modules.articles.schemas.article import ArticleCreate, ArticleFilters


class ArticleService:
    @staticmethod
    def search_articles(
        db: Session, filters: ArticleFilters, skip: int = 0, limit: int = 10
    ) -> tuple[list[Article], str]:

        allowed_sort_fields = {"category", "views", "published_at"}
        stmt = select(Article)

        # Apply filters
        if filters.category:
            stmt = stmt.where(Article.category.ilike(f"%{filters.category}%"))
        if filters.source:
            stmt = stmt.where(Article.source.ilike(f"%{filters.source}%"))
        if filters.keyword:
            stmt = stmt.where(
                Article.title.ilike(f"%{filters.keyword}%")
                | Article.content.ilike(f"%{filters.keyword}%")
            )

        if filters.start_date and filters.end_date:
            stmt = stmt.where(
                Article.published_at.between(filters.start_date, filters.end_date)
            )
        elif filters.start_date:
            stmt = stmt.where(Article.published_at >= filters.start_date)
        elif filters.end_date:
            stmt = stmt.where(Article.published_at <= filters.end_date)

        # Sorting
        # Verify column existence
        if filters.sort_by not in allowed_sort_fields:
            raise BadRequestError(
                message="Invalid field", detail=f"Invalid sort field: {filters.sort_by}"
            )

        sort_column = getattr(Article, filters.sort_by, None)
        if sort_column:
            stmt = stmt.order_by(
                sort_column.desc() if filters.order == "desc" else sort_column.asc()
            )

        # Get total count
        total_count = db.execute(
            select(func.count()).select_from(stmt.subquery())
        ).scalar()

        # Apply pagination
        articles = db.execute(stmt.limit(limit).offset(skip)).scalars().all()

        return articles, str(total_count)

    @staticmethod
    def create_article(db: Session, article_data: ArticleCreate) -> Article:
        stmt = (
            insert(Article)
            .values(**article_data.model_dump())
            .on_conflict_do_nothing(index_elements=["url"])
            .returning(Article)
        )

        article = db.execute(stmt).scalar_one_or_none()
        db.commit()

        if not article:
            raise ConflictError("Article with this URL already exists")

        return article

    @staticmethod
    def get_article_by_id(db: Session, article_id: UUID) -> Article:
        article = db.execute(
            select(Article).where(Article.id == article_id)
        ).scalar_one_or_none()
        if not article:
            raise NotFoundError(resource="article", identifier=article_id)

        return article

    @staticmethod
    def delete_article(db: Session, article_id: UUID) -> None:
        current_time = datetime.now(timezone.utc)
        stmt = (
            update(Article)
            .where((Article.id == article_id) & (Article.is_deleted == False))
            .values(is_deleted=True, deleted_at=current_time)
            .returning(Article.id)
        )

        result = db.execute(stmt)
        db.commit()

        if not result.scalar_one_or_none():
            raise NotFoundError(resource="article", identifier=article_id)

    @staticmethod
    def update_article(
        db: Session, article_id: UUID, new_data: ArticleCreate
    ) -> Article:
        # Update the model instance with the fields provided in new_data
        # Only include fields that are set
        stmt = (
            update(Article)
            .where(Article.id == article_id)
            .values(**new_data.model_dump(exclude_unset=True))
            .returning(Article)
        )

        article = db.execute(stmt).scalar_one_or_none()
        db.commit()

        if not article:
            raise NotFoundError(resource="article", identifier=article_id)

        return article

    @staticmethod
    def save_articles_to_db(db: Session, articles_data: list[dict]) -> dict:
        """Recieves articles and saves them to the database."""
        valid_articles = []
        validation_errors = 0

        for article in articles_data:
            try:
                # Clean title using more common separator
                raw_title = article.get("title", "Untitled")
                if " - " in raw_title:
                    title = raw_title.split(" - ")[0].strip()
                else:
                    title = raw_title

                # Validate with Pydantic model
                article_data = ArticleCreate(
                    title=title,
                    content=article.get("description") or "No content available",
                    source=article.get("source", {}).get("name") or "Unknown",
                    url=article["url"],  # Mandatory field
                    published_at=datetime.fromisoformat(article["publishedAt"]),
                )
                valid_articles.append(article_data.model_dump())

            except (KeyError, ValidationError) as e:
                validation_errors += 1
                logger.warning("Skipping invalid article: %s", e)
                continue

        if not valid_articles:
            logger.info("No valid articles to save")
            return {"saved": 0, "errors": validation_errors}

        try:
            stmt = insert(Article).values(valid_articles)
            stmt = stmt.on_conflict_do_update(
                index_elements=["url"],
                set_={
                    "title": stmt.excluded.title,
                    "content": stmt.excluded.content,
                    "published_at": stmt.excluded.published_at,
                },
            )

            result = db.execute(stmt)
            db.commit()

            logger.info(
                "Saved %d articles (%d validation errors)",
                len(valid_articles),
                validation_errors,
            )
            return {"saved": len(valid_articles), "errors": validation_errors}

        except SQLAlchemyError as e:
            logger.error("Database error: %s", e, exc_info=True)
            db.rollback()
            raise ServerError("Failed to save articles") from e
