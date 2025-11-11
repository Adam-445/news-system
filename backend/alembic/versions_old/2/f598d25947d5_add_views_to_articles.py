"""add_views_to_articles

Revision ID: f598d25947d5
Revises: 93f667af0dc1
Create Date: 2025-02-09 21:25:25.160573

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f598d25947d5"
down_revision: Union[str, None] = "93f667af0dc1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column(
        "articles", sa.Column("views", sa.Integer, server_default="0", nullable=False)
    )


def downgrade():
    op.drop_column("articles", "views")
