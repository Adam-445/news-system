"""Implemented roles using roles and permissions tables 

Revision ID: 609d2f59a701
Revises: 695c4c1ebd15
Create Date: 2025-02-05 13:51:28.758037

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '609d2f59a701'
down_revision: Union[str, None] = '695c4c1ebd15'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_foreign_key(None, 'users', 'roles', ['role_name'], ['name'])


def downgrade() -> None:
    op.drop_constraint(None, 'users', type_='foreignkey')
