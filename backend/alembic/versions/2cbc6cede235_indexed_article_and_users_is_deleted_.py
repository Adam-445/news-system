"""Indexed article and users is_deleted attribute

Revision ID: 2cbc6cede235
Revises: 4b29c327c784
Create Date: 2025-02-28 22:31:01.493624

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2cbc6cede235'
down_revision: Union[str, None] = '4b29c327c784'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(op.f('ix_articles_deleted_at'), 'articles', ['deleted_at'], unique=False)
    op.create_index(op.f('ix_users_is_deleted'), 'users', ['is_deleted'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_users_is_deleted'), table_name='users')
    op.drop_index(op.f('ix_articles_deleted_at'), table_name='articles')
