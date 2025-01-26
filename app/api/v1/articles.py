from typing import List
from app.db.database import get_db
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
import app.schemas as schemas
from app.crud.articles import ArticleService

router = APIRouter()

@router.get("/", response_model=List[schemas.ArticleResponse])
def get_articles(db: Session = Depends(get_db)):
    """
    Fetch all articles from the database.
    """
    return ArticleService.get_all_articles(db)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.ArticleResponse)
def create_article(article: schemas.ArticleCreate, db: Session = Depends(get_db)):
    """
    Create a new article.
    """
    return ArticleService.create_article(db, article)


@router.get("/{id}", response_model=schemas.ArticleResponse)
def get_article(id: int, db: Session = Depends(get_db)):
    """
    Fetch a single article by ID.
    """
    article = ArticleService.get_article_by_id(db, id)
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article with id {id} was not found.",
        )
    return article


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_article(id: int, db: Session = Depends(get_db)):
    """
    Delete an article by ID.
    """
    if not ArticleService.delete_article(db, id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article with id {id} was not found.",
        )


@router.patch("/{id}", response_model=schemas.ArticleResponse)
def update_article(id: int, new_article: schemas.ArticleUpdate, db: Session = Depends(get_db)):
    """
    Update an existing article by ID.
    """
    updated_article = ArticleService.update_article(db, id, new_article)
    if not updated_article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article with id {id} was not found.",
        )
    return updated_article
