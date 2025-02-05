"""add is_active to users to soft delete

Revision ID: 8e2eec88034b
Revises: 99fc2727a550
Create Date: 2025-01-26 13:39:09.687659

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8e2eec88034b"
down_revision: Union[str, None] = "99fc2727a550"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("is_active", sa.Boolean(), server_default="TRUE", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("users", "is_active")
