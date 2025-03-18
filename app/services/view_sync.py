import asyncio

from sqlalchemy.sql import update
from sqlalchemy.sql.expression import bindparam

from app.core.logging import logger
from app.core.redis import RedisManager
from app.db import models
from app.db.database import get_db


class ViewSynchronizer:
    def __init__(self):
        self.batch_size = 1000
        self.retry_limit = 3
        self.backoff_base = 2  # Exponential backoff base

    async def sync(self):
        """Atomic sync with get-and-reset pattern"""
        redis = await RedisManager.get_redis()
        keys = await redis.keys("views:*")

        # Process in chuncks to prevent memomry issues
        for chunck in self._chuncked(keys, self.batch_size):
            await self._process_chunck(chunck)

    def _chuncked(self, list, n):
        """Yield successive n-sized chuncks from lst"""
        for i in range(0, len(list), n):
            yield list[i : i + n]

    async def _process_chunck(self, keys: list[str]):
        article_counts = {}
        redis = await RedisManager.get_redis()

        async with redis.pipeline() as pipe:
            for key in keys:
                pipe.getdel(key)
            results = await pipe.execute()

        # Pair keys with their counts
        for key, count in zip(keys, results[::2]):
            if not count:
                continue
            article_id = key.split(":")[1]
            article_counts[article_id] = int(count)

        if article_counts:
            # Batch update database
            await self._update_database(article_counts)

    async def _update_database(self, counts: dict[str, int]):
        stmt = (
            update(models.Article)
            .where(models.Article.id == bindparam("article_id"))
            .values(views=models.Article.views + bindparam("count"))
        )

        params = [
            {"article_id": article_id, "count": count}
            for article_id, count in counts.items()
        ]

        for attempt in range(self.retry_limit):
            try:
                # Get session manually
                db_gen = get_db()
                db = next(db_gen)

                db.execute(
                    stmt, params, execution_options={"synchronize_session": False}
                )
                db.commit()
                logger.info(f"Updated {len(counts)} articles")

                break
            except Exception as e:
                if attempt == self.retry_limit - 1:
                    logger.error("Final sync attempt failed", exc_info=True)
                    break
                delay = self.backoff_base**attempt
                logger.warning(
                    f"Sync attempt {attempt + 1} failed. Retrying in {delay} seconds"
                )
                await asyncio.sleep(delay)
            finally:
                db.close()
