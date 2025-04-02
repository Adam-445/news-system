from celery import Celery
from app.core.config import settings

celery = Celery(__name__)
celery.conf.update(
    broker_url=settings.celery_broker_url,
    result_backend=settings.celery_result_backend,
    imports=["app.services.scraping"],
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_default_queue="default",
    task_queue={
        'scraping_queue': {
            'exchange': 'scraping',
            'routing_key': 'scraping',
        },
    },
    task_annotations={
        'app.services.scraping.scrape_articles_task': {
            'rate_limit': '10/m',
            'max_retries': 3,
            'default_retry_delay': 60,
        }
    }
)