"""add is_new to exam_papers

Revision ID: 4a6b215aa3e5
Revises: 010
Create Date: 2026-05-06 15:50:37.526435

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4a6b215aa3e5'
down_revision: Union[str, None] = '010'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('exam_papers', sa.Column('is_new', sa.Boolean(), server_default='0', nullable=False))


def downgrade() -> None:
    op.drop_column('exam_papers', 'is_new')
