from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from app.db.database import Base
from .role_permission import role_permission

class Permission(Base):
    __tablename__ = "permissions"
    name = Column(String, primary_key=True, unique=True, index=True)
    description = Column(String, nullable=True)

    roles = relationship("Role", secondary=role_permission, back_populates="permissions")
