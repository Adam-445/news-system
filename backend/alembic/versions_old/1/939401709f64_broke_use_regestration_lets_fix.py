"""Broke use regestration, lets fix

Revision ID: 939401709f64
Revises: 0b9a29d56041
Create Date: 2025-01-29 15:21:35.443060

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '939401709f64'
down_revision: Union[str, None] = '0b9a29d56041'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint('articles_url_key', 'articles', ['url'])


def downgrade() -> None:
    op.drop_constraint('articles_url_key', 'articles', type_='unique')
