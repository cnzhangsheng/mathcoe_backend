"""add status column to questions table

Revision ID: 012
Revises: 4a790179050a
Create Date: 2026-05-19

"""
from alembic import op
import sqlalchemy as sa


revision = '012'
down_revision = '4a790179050a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'questions',
        sa.Column('status', sa.String(length=16), nullable=False, server_default='published')
    )


def downgrade() -> None:
    op.drop_column('questions', 'status')
