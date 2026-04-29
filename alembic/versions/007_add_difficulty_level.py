"""add difficulty_level to users

Revision ID: 007
Revises: 006
Create Date: 2026-04-29

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('difficulty_level', sa.Integer(), nullable=False, server_default='1'))
    op.alter_column('users', 'difficulty_level', server_default=None)


def downgrade():
    op.drop_column('users', 'difficulty_level')
