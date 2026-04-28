"""add likes table

Revision ID: 006
Revises: 005_add_exam_paper_tests
Create Date: 2026-04-28

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade():
    # Create likes table
    op.create_table(
        'likes',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('question_id', sa.BigInteger(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create index for user_id and question_id
    op.create_index('ix_likes_user_id', 'likes', ['user_id'], unique=False)
    op.create_index('ix_likes_question_id', 'likes', ['question_id'], unique=False)


def downgrade():
    op.drop_index('ix_likes_question_id', table_name='likes')
    op.drop_index('ix_likes_user_id', table_name='likes')
    op.drop_table('likes')