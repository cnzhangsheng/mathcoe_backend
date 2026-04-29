"""Initial migration - create all tables

Revision ID: 001
Revises:
Create Date: 2026-04-22

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users table
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("openid", sa.String(64), nullable=False),
        sa.Column("nickname", sa.String(64), nullable=True),
        sa.Column("avatar_url", sa.String(256), nullable=True),
        sa.Column("streak_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_active_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.utcnow()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.utcnow()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("openid"),
    )
    op.create_index("ix_users_openid", "users", ["openid"])

    # Topics table
    op.create_table(
        "topics",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("title", sa.String(64), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("difficulty", sa.String(16), nullable=True),
        sa.Column("icon", sa.String(32), nullable=True),
        sa.Column("color", sa.String(16), nullable=True),
        sa.Column("is_high_freq", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.utcnow()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.utcnow()),
        sa.PrimaryKeyConstraint("id"),
    )

    # Questions table
    op.create_table(
        "questions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("topic_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("content", sa.JSON(), nullable=True),
        sa.Column("answer", sa.String(8), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("difficulty", sa.String(16), nullable=True),
        sa.Column("source_year", sa.Integer(), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=True, server_default="[]"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.utcnow()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.utcnow()),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["topic_id"], ["topics.id"]),
    )
    op.create_index("ix_questions_topic_id", "questions", ["topic_id"])

    # Practice records table
    op.create_table(
        "practice_records",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.Integer(), nullable=False),
        sa.Column("user_answer", sa.String(8), nullable=True),
        sa.Column("is_correct", sa.Boolean(), nullable=True),
        sa.Column("time_spent", sa.Integer(), nullable=True),
        sa.Column("is_flagged", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_bookmarked", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.utcnow()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.utcnow()),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"]),
    )
    op.create_index("ix_practice_records_user_id", "practice_records", ["user_id"])

    # Favorites table
    op.create_table(
        "favorites",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.utcnow()),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"]),
        sa.UniqueConstraint("user_id", "question_id", name="uq_user_question_favorite"),
    )

    # Wrong questions table
    op.create_table(
        "wrong_questions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.Integer(), nullable=False),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_retry_at", sa.DateTime(), nullable=True),
        sa.Column("mastered", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.utcnow()),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"]),
        sa.UniqueConstraint("user_id", "question_id", name="uq_user_question_wrong"),
    )


def downgrade() -> None:
    op.drop_table("wrong_questions")
    op.drop_table("favorites")
    op.drop_table("practice_records")
    op.drop_table("questions")
    op.drop_table("topics")
    op.drop_table("users")