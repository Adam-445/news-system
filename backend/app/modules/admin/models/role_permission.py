from sqlalchemy import Column, ForeignKey, String, Table

from backend.app.shared.db.base import Base

role_permission = Table(
    "role_permission",
    Base.metadata,
    Column("role_name", String, ForeignKey("roles.name"), primary_key=True),
    Column("permission_name", String, ForeignKey("permissions.name"), primary_key=True),
)
