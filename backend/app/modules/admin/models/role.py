from sqlalchemy import Column, String, Text
from sqlalchemy.orm import relationship

from backend.app.modules.admin.models.role_permission import role_permission
from backend.app.shared.db.base import Base


class Role(Base):
    __tablename__ = "roles"
    name = Column(String, primary_key=True, unique=True, index=True)
    description = Column(Text, nullable=True)

    permissions = relationship(
        "Permission", secondary=role_permission, back_populates="roles", lazy="selectin"
    )

    users = relationship("User", back_populates="role", lazy="selectin")
