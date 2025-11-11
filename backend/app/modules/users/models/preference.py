from sqlalchemy import JSON, Column, ForeignKey, Integer, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.app.shared.db.base import Base


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    # PostgreSQL-safe JSON array
    saved_articles = Column(JSON, default=text("'[]'::json"))
    preferred_categories = Column(JSON, default=[])
    preferred_sources = Column(JSON, default=[])

    user = relationship("User", back_populates="preferences")
