from sqlalchemy import TIMESTAMP, Column, Integer, String, Boolean, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text
from sqlalchemy.sql.sqltypes import TIMESTAMP
import uuid
import enum

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    username = Column(String, nullable=False, unique=True, index=True)
    email = Column(String, nullable=False, unique=True, index=True)
    password = Column(String, nullable=False)

    is_deleted = Column(Boolean, server_default="FALSE", nullable=False)
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)

    role_name = Column(String, ForeignKey("roles.name"), nullable=False)
    role = relationship("Role", back_populates="users", lazy="joined")

    created_at = Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("NOW()")
    )
    preferences = relationship("UserPreference", uselist=False)
