from sqlalchemy import TIMESTAMP, Boolean, Column, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql.expression import text
from sqlalchemy.sql.sqltypes import TIMESTAMP

from app.db.base import Base

# For article metadata
# from sqlalchemy.dialects.postgresql import JSONB


class Article(Base):
    __tablename__ = "articles"

    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    source = Column(String(100), index=True)
    category = Column(String(50), index=True)
    url = Column(String, nullable=False, unique=True)

    views = Column(Integer, server_default="0", nullable=False, index=True)

    is_deleted = Column(Boolean, server_default="FALSE")
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True, index=True)

    published_at = Column(TIMESTAMP(timezone=True), index=True, nullable=True)
    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
