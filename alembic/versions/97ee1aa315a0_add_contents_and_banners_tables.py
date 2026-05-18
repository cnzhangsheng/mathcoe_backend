"""add contents and banners tables

Revision ID: 97ee1aa315a0
Revises: 011
Create Date: 2026-05-18 14:24:01.609720

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = '97ee1aa315a0'
down_revision: Union[str, None] = '011'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('banners',
    sa.Column('image_url', sa.String(length=512), nullable=False),
    sa.Column('link_type', sa.String(length=16), nullable=False),
    sa.Column('link_value', sa.String(length=512), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('sort_order', sa.Integer(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('id', sa.BigInteger(), autoincrement=False, nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('contents',
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('slug', sa.String(length=128), nullable=False),
    sa.Column('status', sa.String(length=16), nullable=False),
    sa.Column('id', sa.BigInteger(), autoincrement=False, nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('slug')
    )


def downgrade() -> None:
    op.drop_table('contents')
    op.drop_table('banners')
