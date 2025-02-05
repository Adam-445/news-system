"""added role to users table

Revision ID: 695c4c1ebd15
Revises: a2fe612f2d29
Create Date: 2025-02-03 11:45:42.096246

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "695c4c1ebd15"
down_revision: Union[str, None] = "a2fe612f2d29"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column(
        "users",
        sa.Column("role_name", sa.String(), server_default="regular", nullable=False),
    )


def downgrade():
    op.drop_column("users", "role_name")
