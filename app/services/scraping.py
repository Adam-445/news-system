import asyncio
import random
import json
from typing import List, Dict

import httpx
from celery import Task
from sqlalchemy.orm import Session

from app.core.celery import celery
from app.core.config import settings
from app.core.logging import logger
from app.crud.articles import ArticleService
from app.db.database import get_db

API_KEY = settings.api_key
BASE_URL = "https://newsapi.org/v2/top-headlines"
PAGE_SIZE = 50
MAX_RETRIES = 3
BASE_RETRY_DELAY = 2  # Base delay in seconds


class ScrapingError(Exception):
    """Custom exception for scraping-related errors"""

    def __init__(self, message: str, recoverable: bool = True):
        self.recoverable = recoverable
        super().__init__(message)


def calculate_retry_delay(retries: int) -> int:
    """Calculate exponential backoff with jitter"""
    jitter = random.uniform(0.9, 1.1)  # ±10% jitter
    return int((BASE_RETRY_DELAY**retries) * jitter)


async def fetch_page(client: httpx.AsyncClient, page: int) -> List[Dict]:
    """Fetch a single page of articles"""
    try:
        response = await client.get(
            BASE_URL,
            params={
                "language": "en",
                "pageSize": PAGE_SIZE,
                "page": page,
                "apiKey": API_KEY,
            },
            timeout=10.0,
        )
        response.raise_for_status()
        return response.json().get("articles", [])
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            retry_after = int(e.response.headers.get("Retry-After", 5))
            raise ScrapingError(f"Rate limited. Retry after {retry_after}s", True)
        raise ScrapingError(f"HTTP error {e.response.status_code}", False)
    except json.JSONDecodeError:
        raise ScrapingError("Invalid JSON response", False)


async def scrape_via_api(max_pages: int = 3) -> List[Dict]:
    """Main scraping logic with error handling"""
    if not API_KEY:
        raise ScrapingError("API key is missing", False)

    all_articles = []
    async with httpx.AsyncClient() as client:
        for page in range(1, max_pages + 1):
            try:
                articles = await fetch_page(client, page)
                if not articles:
                    break
                all_articles.extend(articles)
                logger.info(f"Fetched {len(articles)} articles from page {page}")
            except ScrapingError as e:
                if not e.recoverable:
                    raise
                await asyncio.sleep(5)  # Wait before retrying
    return all_articles

@celery.task(
    bind=True,
    queue="scraping_queue",
    autoretry_for=(ScrapingError,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=MAX_RETRIES
)
def scrape_articles_task(self: Task) -> Dict:
    """Celery task to handle article scraping and saving"""
    db: Session = next(get_db())
    try:
        articles_data = asyncio.run(scrape_via_api())

        if not articles_data:
            logger.warning("No articles to save")
            return {"count": 0}

        # Synchronous database operation
        result = ArticleService.save_articles_to_db(db, articles_data)
        db.commit()
        logger.info(f"Successfully saved {result.get('saved', 0)} articles")
        return result

    except ScrapingError as e:
        logger.error(f"Scraping failed: {str(e)}")
        db.rollback()
        self.retry(exc=e, countdown=calculate_retry_delay(self.request.retries))
    except Exception as e:
        logger.exception("Unexpected error occurred")
        db.rollback()
        self.retry(exc=e, countdown=calculate_retry_delay(self.request.retries))
    finally:
        db.close()

    return {"error": "Task failed after maximum retries"}