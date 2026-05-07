"""add file_path to exam_papers

Revision ID: e61e008cd441
Revises: 4a6b215aa3e5
Create Date: 2026-05-07 12:32:34.595939

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e61e008cd441'
down_revision: Union[str, None] = '4a6b215aa3e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('exam_papers', sa.Column('file_path', sa.String(256), nullable=True))


def downgrade() -> None:
    op.drop_column('exam_papers', 'file_path')
