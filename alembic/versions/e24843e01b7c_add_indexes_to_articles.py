"""add_indexes_to_articles

Revision ID: e24843e01b7c
Revises: f598d25947d5
Create Date: 2025-02-14 20:17:25.944153

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e24843e01b7c"
down_revision: Union[str, None] = "f598d25947d5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_index("ix_articles_views", "articles", ["views"])
    op.create_index("ix_articles_category", "articles", ["category"])
    op.create_index(
        "ix_articles_published_at_views", "articles", ["published_at", "views"]
    )


def downgrade():
    op.drop_index("ix_articles_views")
    op.drop_index("ix_articles_category")
    op.drop_index("ix_articles_published_at_views")
