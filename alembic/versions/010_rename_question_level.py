"""rename questions.level to difficulty_level

Revision ID: 010
Revises: 009
Create Date: 2026-04-29

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '010'
down_revision = '009'
branch_labels = None
depends_on = None


def upgrade():
    # Drop old index
    op.drop_index('ix_questions_level', table_name='questions')

    # Rename column
    op.alter_column('questions', 'level', new_column_name='difficulty_level',
                    type_=sa.Integer())

    # Create new index
    op.create_index('ix_questions_difficulty_level', 'questions', ['difficulty_level'], unique=False)


def downgrade():
    op.drop_index('ix_questions_difficulty_level', table_name='questions')

    op.alter_column('questions', 'difficulty_level', new_column_name='level',
                    type_=sa.Integer())

    op.create_index('ix_questions_level', 'questions', ['level'], unique=False)
