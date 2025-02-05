from typing import List
from fastapi import APIRouter, Depends, status, HTTPException, BackgroundTasks, Response
from sqlalchemy.orm import Session

from app.db.database import get_db
import app.schemas as schemas
from app.crud.articles import ArticleService
from app.api.dependencies import get_current_user, required_roles
from app.db import models

router = APIRouter()


@router.get("/", response_model=List[schemas.ArticleResponse])
def get_articles(
    response: Response, skip: int = 0, limit: int = 10, db: Session = Depends(get_db)
):
    """
    Fetch articles with pagination support.
    """
    articles, article_count = ArticleService.get_all_articles(
        db, skip=skip, limit=limit
    )
    response.headers["X-Total-Count"] = str(article_count)
    return articles


@router.post(
    "/", status_code=status.HTTP_201_CREATED, response_model=schemas.ArticleResponse
)
def create_article(
    article: schemas.ArticleCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(required_roles(["admin", "moderator"])),
):
    """
    Create a new article.
    """
    article = ArticleService.create_article(db, article)
    if not article:
        raise HTTPException(status_code=500, detail=f"Error creating article.")
    return article


@router.get("/{id}", response_model=schemas.ArticleResponse)
def get_article(
    id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
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
def delete_article(
    id: int,
    current_user: models.User = Depends(required_roles(["admin", "moderator"])),
    db: Session = Depends(get_db),
):
    """
    Delete an article by ID.
    """
    if not ArticleService.delete_article(db, id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article with id {id} was not found.",
        )


@router.patch("/{id}", response_model=schemas.ArticleResponse)
def update_article(
    id: int,
    new_article: schemas.ArticleUpdate,
    current_user: models.User = Depends(required_roles(["admin", "moderator"])),
    db: Session = Depends(get_db),
):
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


@router.post("/scrape", status_code=status.HTTP_202_ACCEPTED)
async def scrape_and_store_articles(
    background_tasks: BackgroundTasks,
    current_user: models.User = Depends(required_roles(["admin", "moderator"])),
    db: Session = Depends(get_db),
):
    background_tasks.add_task(ArticleService.save_articles_to_db, db)
    return {"message": "Scraping initiated. Articles will be stored shortly."}
