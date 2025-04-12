"""add users table

Revision ID: 99fc2727a550
Revises: 136d72657ce3
Create Date: 2025-01-26 10:16:39.827874

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
import uuid


# revision identifiers, used by Alembic.
revision: str = "99fc2727a550"
down_revision: Union[str, None] = "136d72657ce3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("username", sa.String(), unique=True, nullable=False, index=True),
        sa.Column("email", sa.String(), unique=True, nullable=False, index=False),
        sa.Column("password", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )


def downgrade() -> None:
    op.drop_table("users")
