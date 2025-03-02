from sqlalchemy import TIMESTAMP, Boolean, Column, Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text
from sqlalchemy.sql.sqltypes import TIMESTAMP

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        index=True,
    )
    username = Column(String, nullable=False, unique=True, index=True)
    email = Column(String, nullable=False, unique=True, index=True)
    password = Column(String(128), nullable=False)

    is_deleted = Column(Boolean, server_default="FALSE", nullable=False, index=True)
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)

    role_name = Column(String, ForeignKey("roles.name"), nullable=False)
    role = relationship("Role", back_populates="users", lazy="selectin")

    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    preferences = relationship("UserPreference", uselist=False)
