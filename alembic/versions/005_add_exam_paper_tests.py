"""add exam_paper_tests table

Revision ID: 005
Revises: 004
Create Date: 2024-04-24

"""
from alembic import op
import sqlalchemy as sa


revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'exam_paper_tests',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('exam_paper_id', sa.BigInteger(), nullable=False),
        sa.Column('score', sa.Integer(), nullable=True),
        sa.Column('correct_count', sa.Integer(), nullable=True),
        sa.Column('total_questions', sa.Integer(), nullable=False),
        sa.Column('time_spent', sa.Integer(), nullable=True),
        sa.Column('answers', sa.JSON(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('finished_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(16), nullable=False, default='in_progress'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['exam_paper_id'], ['exam_papers.id']),
    )


def downgrade():
    op.drop_table('exam_paper_tests')