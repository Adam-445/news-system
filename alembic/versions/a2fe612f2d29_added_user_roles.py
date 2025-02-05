"""added user roles

Revision ID: a2fe612f2d29
Revises: b80b090902a9
Create Date: 2025-02-03 11:01:50.578356

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a2fe612f2d29"
down_revision: Union[str, None] = "b80b090902a9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        'roles',
        sa.Column('name', sa.String(), primary_key=True, unique=True, index=True),
        sa.Column('description', sa.Text(), nullable=True),
    )
    
    op.create_table(
        'permissions',
        sa.Column('name', sa.String(), primary_key=True, unique=True, index=True),
        sa.Column('description', sa.String(), nullable=True),
    )
    
    op.create_table(
        'role_permission',
        sa.Column('role_name', sa.String(), sa.ForeignKey('roles.name'), primary_key=True),
        sa.Column('permission_name', sa.String(), sa.ForeignKey('permissions.name'), primary_key=True)
    )

def downgrade():
    op.drop_table('role_permission')
    op.drop_table('permissions')
    op.drop_table('roles')
