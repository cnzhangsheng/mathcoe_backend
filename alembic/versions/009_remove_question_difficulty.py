"""remove question.difficulty column

Revision ID: 009
Revises: 008
Create Date: 2026-04-29

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '009'
down_revision = '008'
branch_labels = None
depends_on = None


def upgrade():
    # Drop index on difficulty column
    op.drop_index('ix_questions_difficulty', table_name='questions')

    # Drop the column
    op.drop_column('questions', 'difficulty')


def downgrade():
    # Add column back
    op.add_column('questions', sa.Column(
        'difficulty', sa.String(16), nullable=True
    ))

    # Recreate index
    op.create_index('ix_questions_difficulty', 'questions', ['difficulty'], unique=False)
