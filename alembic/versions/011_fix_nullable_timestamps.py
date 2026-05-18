"""fix nullable created_at/updated_at in exam_paper_tests and likes

Revision ID: 011
Revises: e61e008cd441
Create Date: 2026-05-18

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


revision = '011'
down_revision = 'e61e008cd441'
branch_labels = None
depends_on = None


def upgrade():
    # Fix exam_paper_tests: backfill null timestamps, then set nullable+default
    op.execute(text("UPDATE exam_paper_tests SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL"))
    op.execute(text("UPDATE exam_paper_tests SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL"))
    op.alter_column('exam_paper_tests', 'created_at',
                    existing_type=sa.DateTime(),
                    nullable=False,
                    server_default=text('CURRENT_TIMESTAMP'))
    op.alter_column('exam_paper_tests', 'updated_at',
                    existing_type=sa.DateTime(),
                    nullable=False,
                    server_default=text('CURRENT_TIMESTAMP'))

    # Fix likes: backfill null timestamps, then set nullable+default
    op.execute(text("UPDATE likes SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL"))
    op.execute(text("UPDATE likes SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL"))
    op.alter_column('likes', 'created_at',
                    existing_type=sa.DateTime(),
                    nullable=False,
                    server_default=text('CURRENT_TIMESTAMP'))
    op.alter_column('likes', 'updated_at',
                    existing_type=sa.DateTime(),
                    nullable=False,
                    server_default=text('CURRENT_TIMESTAMP'))


def downgrade():
    # Revert exam_paper_tests
    op.alter_column('exam_paper_tests', 'created_at',
                    existing_type=sa.DateTime(),
                    nullable=True,
                    server_default=None)
    op.alter_column('exam_paper_tests', 'updated_at',
                    existing_type=sa.DateTime(),
                    nullable=True,
                    server_default=None)

    # Revert likes
    op.alter_column('likes', 'created_at',
                    existing_type=sa.DateTime(),
                    nullable=True,
                    server_default=None)
    op.alter_column('likes', 'updated_at',
                    existing_type=sa.DateTime(),
                    nullable=True,
                    server_default=None)
