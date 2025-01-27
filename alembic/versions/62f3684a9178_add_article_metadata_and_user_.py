"""Add article metadata and user preferences

Revision ID: 62f3684a9178
Revises: 8e2eec88034b
Create Date: 2025-01-27 08:32:10.813007

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '62f3684a9178'
down_revision: Union[str, None] = '8e2eec88034b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column('articles', sa.Column('source', sa.String(), nullable=True))
    op.add_column('articles', sa.Column('category', sa.String(), nullable=True))
    op.add_column('articles', sa.Column('embedding', postgresql.JSONB(astext_type=sa.Text()), nullable=True))

    op.drop_constraint('users_email_key', 'users', type_='unique')
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    op.create_table(
        'user_preferences',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('saved_articles', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('preferred_categories', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('preferred_sources', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_table('user_preferences')

    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.create_unique_constraint('users_email_key', 'users', ['email'])

    op.drop_column('articles', 'embedding')
    op.drop_column('articles', 'category')
    op.drop_column('articles', 'source')