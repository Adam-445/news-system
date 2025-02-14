
from sqlalchemy import TIMESTAMP, Column, Integer, String, Text
from sqlalchemy.sql.expression import text
from sqlalchemy.sql.sqltypes import TIMESTAMP
# For article metadata
# from sqlalchemy.dialects.postgresql import JSONB

from app.db.database import Base

class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    source = Column(String)
    category = Column(String, index=True)
    url = Column(String, nullable=False, unique=True)

    views = Column(Integer, server_default="0", nullable=False, index=True)

    published_at = Column(TIMESTAMP(timezone=True), index=True, nullable=True)
    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
