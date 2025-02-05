"""Improved articles table

Revision ID: 93f667af0dc1
Revises: 609d2f59a701
Create Date: 2025-02-05 16:11:10.787727

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "93f667af0dc1"
down_revision: Union[str, None] = "609d2f59a701"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # VARCHAR to Text
    op.alter_column(
        "articles",
        "content",
        existing_type=sa.VARCHAR(),
        type_=sa.Text(),
        existing_nullable=False,
    )

    # Drop redundant index on 'id'
    op.drop_index("ix_articles_id", table_name="articles")

    # Drop redundant index on 'url'
    op.drop_index("ix_articles_url", table_name="articles")

    # Create the index on 'published_at' for efficient sorting/filtering
    op.create_index(
        op.f("ix_articles_published_at"), "articles", ["published_at"], unique=False
    )

    # Create the unique constraint on url
    op.create_unique_constraint(None, "articles", ["url"])


def downgrade() -> None:
    op.drop_constraint(None, "articles", type_="unique")

    op.drop_index(op.f("ix_articles_published_at"), table_name="articles")

    op.create_index("ix_articles_url", "articles", ["url"], unique=True)

    op.create_index("ix_articles_id", "articles", ["id"], unique=False)

    op.alter_column(
        "articles",
        "content",
        existing_type=sa.Text(),
        type_=sa.VARCHAR(),
        existing_nullable=False,
    )
