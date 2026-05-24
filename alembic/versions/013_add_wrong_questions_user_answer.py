"""add user_answer column to wrong_questions table

Revision ID: 013
Revises: 7114715dea9d
Create Date: 2026-05-24

"""
from alembic import op
import sqlalchemy as sa


revision = '013'
down_revision = '7114715dea9d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('wrong_questions', sa.Column('user_answer', sa.String(length=8), nullable=True))


def downgrade() -> None:
    op.drop_column('wrong_questions', 'user_answer')
