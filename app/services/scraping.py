import httpx
from app.core.config import settings
import logging

api_key = settings.api_key
page_size = 50
url = f"https://newsapi.org/v2/top-headlines?language=en&pageSize={page_size}&apiKey={api_key}"

logger = logging.getLogger(__name__)

async def scrape_via_api():
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            all_articles = response.json().get("articles", [])

        if not all_articles:
            logger.warning("No articles found in API response.")

        logger.info("Fetched %d articles", len(all_articles))
        return all_articles  # Return raw data for processing elsewhere

    except httpx.TimeoutException:
        logger.error("Request to news API timed out")
        return []
    except httpx.HTTPStatusError as e:
        logger.error("Error fetching news articles: %s", e)
        return []
    except Exception as e:
        logger.error("Unexpected error: %s", e)
        return []