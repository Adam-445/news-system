from app.db.database import Base

from sqlalchemy import TIMESTAMP, Column, Integer, String, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql.expression import text
from sqlalchemy.sql.sqltypes import TIMESTAMP
import uuid


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password = Column(String, nullable=False)
    is_active = Column(Boolean, server_default="TRUE" ,nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("NOW()"))
        