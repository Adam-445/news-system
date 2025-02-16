from sqlalchemy import create_engine
from app.core.config import settings

SQLALCHEMY_DATABASE_URL = (
    f"postgresql://{settings.database_username}:{settings.database_password}"
    f"@{settings.database_hostname}:{settings.database_port}/{settings.database_name}"
)

engine = create_engine(
    SQLALCHEMY_DATABASE_URL
)
