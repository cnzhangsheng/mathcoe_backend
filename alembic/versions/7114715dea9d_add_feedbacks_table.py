"""add feedbacks table

Revision ID: 7114715dea9d
Revises: 55d0f64f01aa
Create Date: 2026-05-22 12:29:16.645406

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '7114715dea9d'
down_revision: Union[str, None] = '55d0f64f01aa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('feedbacks',
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('contact', sa.String(length=64), nullable=True),
        sa.Column('status', sa.String(length=16), nullable=False),
        sa.Column('admin_reply', sa.Text(), nullable=True),
        sa.Column('id', sa.BigInteger(), autoincrement=False, nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_feedbacks_user_id'), 'feedbacks', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_feedbacks_user_id'), table_name='feedbacks')
    op.drop_table('feedbacks')