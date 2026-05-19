"""add_exam_paper_user_id

Revision ID: 55d0f64f01aa
Revises: 012
Create Date: 2026-05-19 11:36:07.923028

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '55d0f64f01aa'
down_revision: Union[str, None] = '012'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('exam_papers', sa.Column('user_id', sa.BigInteger(), nullable=True))
    op.add_column('exam_papers', sa.Column('generation_config', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('exam_papers', 'generation_config')
    op.drop_column('exam_papers', 'user_id')
