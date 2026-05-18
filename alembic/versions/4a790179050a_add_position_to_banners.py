"""add position to banners

Revision ID: 4a790179050a
Revises: 97ee1aa315a0
Create Date: 2026-05-18 14:53:38.373282

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '4a790179050a'
down_revision: Union[str, None] = '97ee1aa315a0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('banners', sa.Column('position', sa.String(length=32), server_default='home', nullable=False))


def downgrade() -> None:
    op.drop_column('banners', 'position')
