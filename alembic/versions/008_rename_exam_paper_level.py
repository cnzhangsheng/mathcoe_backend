"""rename exam_papers.level to difficulty_level

Revision ID: 008
Revises: 007
Create Date: 2026-04-29

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade():
    # Drop old index
    op.drop_index('ix_exam_papers_level', table_name='exam_papers')

    # Alter column: drop old VARCHAR column, add new INTEGER column
    op.alter_column('exam_papers', 'level', new_column_name='difficulty_level',
                    type_=sa.Integer(), postgresql_using='CASE level WHEN \'A\' THEN 1 WHEN \'B\' THEN 2 WHEN \'C\' THEN 3 WHEN \'D\' THEN 4 WHEN \'E\' THEN 5 WHEN \'F\' THEN 6 ELSE 1 END')
    op.alter_column('exam_papers', 'difficulty_level', server_default='1', nullable=False)

    # Create new index
    op.create_index('ix_exam_papers_difficulty_level', 'exam_papers', ['difficulty_level'], unique=False)


def downgrade():
    op.drop_index('ix_exam_papers_difficulty_level', table_name='exam_papers')

    op.alter_column('exam_papers', 'difficulty_level', new_column_name='level',
                    type_=sa.String(2),
                    postgresql_using='CASE difficulty_level WHEN 1 THEN \'A\' WHEN 2 THEN \'B\' WHEN 3 THEN \'C\' WHEN 4 THEN \'D\' WHEN 5 THEN \'E\' WHEN 6 THEN \'F\' ELSE \'A\' END')
    op.alter_column('exam_papers', 'level', nullable=False)

    op.create_index('ix_exam_papers_level', 'exam_papers', ['level'], unique=False)
