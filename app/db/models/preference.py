from sqlalchemy import Column, Integer, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.db.database import Base

class UserPreference(Base):
    id = Column(Integer, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    saved_articles = Column(JSON, default=[])
    preferred_categories = Column(JSON, default=[])
    preferred_sources = Column(JSON, default=[])