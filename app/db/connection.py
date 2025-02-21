from sqlalchemy import create_engine

from app.core.config import settings

SQLALCHEMY_DATABASE_URL = settings.database_url
engine = create_engine(
    SQLALCHEMY_DATABASE_URL
)
