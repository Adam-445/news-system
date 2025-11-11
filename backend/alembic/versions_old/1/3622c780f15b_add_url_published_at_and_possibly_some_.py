"""Add url, published at and possibly some other things

Revision ID: 3622c780f15b
Revises: 62f3684a9178
Create Date: 2025-01-27 10:26:14.145790

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "3622c780f15b"
down_revision: Union[str, None] = "62f3684a9178"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("articles", sa.Column("url", sa.String(), nullable=False))
    op.add_column(
        "articles",
        sa.Column("published_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )
    op.create_unique_constraint(None, "articles", ["url"])


def downgrade() -> None:
    op.drop_constraint(None, "articles", type_="unique")
    op.drop_column("articles", "published_at")
    op.drop_column("articles", "url")
