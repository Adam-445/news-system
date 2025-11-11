# from gevent import monkey
# monkey.patch_all(ssl=False, aggressive=True, select=True)

from celery import Celery

from backend.app.common.config.settings import settings

celery = Celery(__name__)
celery.conf.update(
    broker_url=settings.celery_broker_url,
    result_backend=settings.celery_result_backend,
    imports=["backend.app.modules.articles.tasks.scraping"],  # Better task organization
    task_serializer="json",
    event_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    worker_prefetch_multiplier=4,  # Optimize for gevent
    worker_max_tasks_per_child=100,  # Prevent memory leaks
    broker_pool_limit=64,  # Match Redis connection pool
    task_default_queue="default",
    task_queues={
        "scraping_queue": {
            "exchange": "scraping",
            "exchange_type": "direct",
            "routing_key": "scraping",
        },
        "high_priority": {
            "exchange": "high_priority",
            "exchange_type": "direct",
            "routing_key": "high_priority",
        },
    },
    task_annotations={
        "backend.app.modules.articles.tasks.scraping.scrape_articles_task": {
            "rate_limit": "10/m",
            "max_retries": 5,
            "default_retry_delay": 30,
            "priority": 5,
            "queue": "scraping_queue",
        }
    },
)
