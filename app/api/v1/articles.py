from typing import List
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Query, Response, status
from sqlalchemy.orm import Session

import app.schemas as schemas
from app.api.dependencies import get_current_user, required_roles
from app.crud.articles import ArticleService
from app.db import models
from app.db.database import get_db
from app.services.recommendation import get_personalized_recommendation

router = APIRouter()


@router.get(
    "/",
    response_model=List[schemas.ArticleResponse],
    summary="Search Articles",
    description="Fetch articles with filters and pagination.",
)
def get_articles(
    response: Response,
    filters: schemas.ArticleFilters = Depends(),
    skip: int = Query(0, ge=0, description="Number of records to skip for pagination"),
    limit: int = Query(
        10, ge=1, le=100, description="Maximum number of records to return"
    ),
    db: Session = Depends(get_db),
):
    articles, article_count = ArticleService.search_articles(
        db, filters=filters, skip=skip, limit=limit
    )
    response.headers["X-Total-Count"] = str(article_count)
    return articles


@router.get(
    "/recommendations",
    response_model=List[schemas.ArticleResponse],
    tags=["Personalization"],
    summary="Get Personalized Recommendations",
    description="Recommends articles based on user preferences and reading history.",
)
def get_recommendations(
    current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)
):
    return get_personalized_recommendation(db, current_user.id).all()


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=schemas.ArticleResponse,
    summary="Create New Article",
    description="Creates a new news article entry. **Requires Admin/Moderator privileges.**",
    response_description="Details of the created article",
)
def create_article(
    article: schemas.ArticleCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(required_roles(["admin", "moderator"])),
):
    return ArticleService.create_article(db, article)


@router.get(
    "/{id}",
    response_model=schemas.ArticleResponse,
    summary="Get Article by ID",
    description="Fetch a single article by its ID. Returns a 404 if not found.",
    responses={404: {"description": "Article not found."}},
)
def get_article(
    id: UUID,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ArticleService.get_article_by_id(db, id)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Article",
    description="Deletes an article by ID. **Requires Admin/Moderator privileges.**",
    responses={
        204: {"description": "Article successfully deleted."},
        403: {"description": "Forbidden. Requires Admin or Moderator role."},
        404: {"description": "Article not found."},
    },
)
def delete_article(
    id: UUID,
    current_user: models.User = Depends(required_roles(["admin", "moderator"])),
    db: Session = Depends(get_db),
):
    ArticleService.delete_article(db, id)


@router.patch(
    "/{id}",
    response_model=schemas.ArticleResponse,
    summary="Update Article",
    description="Update an existing article by ID. **Requires Admin/Moderator privileges.**",
    responses={404: {"description": "Article not found."}},
)
def update_article(
    id: UUID,
    new_article: schemas.ArticleUpdate,
    current_user: models.User = Depends(required_roles(["admin", "moderator"])),
    db: Session = Depends(get_db),
):
    return ArticleService.update_article(db, id, new_article)


@router.post(
    "/scrape",
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Admin Operations"],
    summary="Initiate Article Scraping",
    description="Starts background scraping of news articles from external sources. **Requires Admin privileges.**",
    dependencies=[Depends(required_roles(["admin", "moderator"]))],
)
async def scrape_and_store_articles(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    background_tasks.add_task(ArticleService.save_articles_to_db, db)
    return {"message": "Scraping initiated. Articles will be stored shortly."}
