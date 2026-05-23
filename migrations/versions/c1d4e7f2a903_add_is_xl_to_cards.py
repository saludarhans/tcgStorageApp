"""add is_xl to cards

Revision ID: c1d4e7f2a903
Revises: b9c3f2e1d807
Create Date: 2026-05-22
"""
from alembic import op
import sqlalchemy as sa

revision = 'c1d4e7f2a903'
down_revision = 'b9c3f2e1d807'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('cards',
        sa.Column('is_xl', sa.Boolean(), nullable=True, server_default=sa.false())
    )


def downgrade():
    op.drop_column('cards', 'is_xl')
