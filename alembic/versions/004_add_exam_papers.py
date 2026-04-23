"""Add exam_papers and exam_paper_questions tables

Revision ID: 004
Revises: 003
Create Date: 2026-04-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # exam_papers table
    op.create_table(
        "exam_papers",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("title", sa.String(128), nullable=False),
        sa.Column("level", sa.String(2), nullable=False),
        sa.Column("total_questions", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("paper_type", sa.String(16), nullable=False, server_default="daily"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.utcnow()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.utcnow()),
        sa.PrimaryKeyConstraint("id"),
    )

    # exam_paper_questions table
    op.create_table(
        "exam_paper_questions",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("exam_paper_id", sa.BigInteger(), nullable=False),
        sa.Column("question_id", sa.BigInteger(), nullable=False),
        sa.Column("sort", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.utcnow()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.utcnow()),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["exam_paper_id"], ["exam_papers.id"]),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"]),
    )

    # Update alembic version
    op.execute("UPDATE alembic_version SET version_num='004' WHERE alembic_version.version_num = '003'")


def downgrade() -> None:
    op.drop_table("exam_paper_questions")
    op.drop_table("exam_papers")
    op.execute("UPDATE alembic_version SET version_num='003' WHERE alembic_version.version_num = '004'")