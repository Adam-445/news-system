from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

from backend.app.common.config.settings import settings

SQLALCHEMY_DATABASE_URL = settings.database_url
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=10,
    pool_timeout=30
)
