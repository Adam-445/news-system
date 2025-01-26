from sqlalchemy.orm import Session
from app.db import models
from app.schemas import ArticleCreate


class ArticleService:
    @staticmethod
    def get_all_articles(db: Session):
        return db.query(models.Article).all()

    @staticmethod
    def create_article(db: Session, article_data: ArticleCreate):
        article = models.Article(**article_data.model_dump())
        db.add(article)
        db.commit()
        db.refresh(article)
        return article

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
