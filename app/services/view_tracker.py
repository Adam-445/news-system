import asyncio
from collections import defaultdict
from contextlib import suppress
from uuid import UUID

from app.core.logging import logger
from app.core.redis import RedisManager


class ViewTracker:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.__initialized = False
        return cls._instance

    def __init__(self):
        if self.__initialized:
            return
        self.__initialized = True
        self.buffer: dict[str, int] = defaultdict(int)
        self.lock = asyncio.Lock()
        self.batch_size = 500
        self.timeout = 60  # Seconds before forcing a flush
        self._flush_task = None

    async def increment(self, article_id: UUID):
        async with self.lock:
            self.buffer[str(article_id)] += 1

            # Flush when threshold is reached
            if len(self.buffer) >= self.batch_size:
                await self._flush()

    async def start_periodic_flush(self):
        """Start background flushing task"""
        self._flush_task = asyncio.create_task(self._periodic_flush())

    async def stop_periodic_flush(self):
        """Stop background flushing task"""
        if self._flush_task:
            self._flush_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._flush_task

    async def _periodic_flush(self):
        """Ensure eventual consistency even during low traffic"""
        while True:
            await asyncio.sleep(self.timeout)
            await self._flush()

    async def _flush(self):
        if not self.buffer:
            return
        try:
            redis = await RedisManager.get_redis()
            async with redis.pipeline() as pipe:
                for aid, count in self.buffer.items():
                    pipe.incrby(f"views:{aid}", count)
                await pipe.execute()

            logger.info(f"Flushed {len(self.buffer)} view increments")
            self.buffer.clear()
        except Exception as e:
            logger.error("Error flushing view increments", exc_info=e)


view_tracker = ViewTracker()
