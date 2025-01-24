from typing import List
from app.db.database import get_db
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
import app.db.models as models
import app.schemas as schemas

router = APIRouter()

@router.get("/", response_model=List[schemas.ArticleResponse])
def get_articles(db: Session = Depends(get_db)):
    articles = db.query(models.Article).all()
    return articles


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.ArticleResponse)
def create_post(article: schemas.ArticleCreate, db: Session = Depends(get_db)):
    article = models.Article(**article.model_dump())
    db.add(article)
    db.commit()
    db.refresh(article)
    return article


@router.get("/{id}", response_model=schemas.ArticleResponse)
def get_article(id: int, db: Session = Depends(get_db)):
    article = db.query(models.Article).filter(models.Article.id == id).first()
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article with id {id} was not found.",
        )
    else:
        return article


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_article(id: int, db: Session = Depends(get_db)):
    article = db.query(models.Article).filter(models.Article.id == id)
    if not article.first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article with id {id} was not found.",
        )
    article.delete(synchronize_session=False)
    db.commit()


@router.put("/{id}", response_model=schemas.ArticleResponse)
def update_post(id: int, new_article: schemas.ArticleCreate, db: Session = Depends(get_db)):
    article = db.query(models.Post).filter(models.Post.id == id)

    if not article.first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article with id {id} was not found.",
        )
    else:
        article.update(new_article.model_dump(), synchronize_session=False)
        db.commit()
        return article.first()