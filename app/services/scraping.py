import asyncio
import json
import logging

import httpx

from app.core.config import settings
from app.core.logging import logger

# logger = logging.getLogger(__name__)


API_KEY = settings.api_key
BASE_URL = "https://newsapi.org/v2/top-headlines"
PAGE_SIZE = 50  # Max results per request

async def scrape_via_api(max_pages: int = 3) -> list[dict[str, any]]:
    """
    Fetches articles from the news API with pagination.

    Args:
        max_pages (int): The maximum number of pages to fetch.

    Returns:
        list: A list of articles retrieved from the API.
    """
    if not API_KEY:
        logger.error("API key is missing! Check your settings.")
        return []

    all_articles = []

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            for page in range(1, max_pages + 1):
                params = {
                    "language": "en",
                    "pageSize": PAGE_SIZE,
                    "page": page,
                    "apiKey": API_KEY,
                }

                response = await client.get(BASE_URL, params=params)
                response.raise_for_status()

                try:
                    data = response.json()
                except json.JSONDecodeError:
                    logger.error("Failed to parse JSON response")
                    return []

                articles = data.get("articles", [])
                if not articles:
                    logger.warning("No articles found on page %d", page)
                    break

                all_articles.extend(articles)

                logger.info("Fetched %d articles from page %d", len(articles), page)

                # Handle rate limits (if API returns `Retry-After` header)
                if "Retry-After" in response.headers:
                    retry_after = int(response.headers["Retry-After"])
                    logger.warning("Rate limit reached. Retrying after %d seconds...", retry_after)
                    await asyncio.sleep(retry_after)
                    # Retry the current page
                    continue

    except httpx.TimeoutException:
        logger.error("Request to news API timed out")
    except httpx.HTTPStatusError as e:
        logger.error("HTTP error fetching news articles: %s", e)
    except Exception as e:
        logger.error("Unexpected error: %s", e)

    return all_articles
