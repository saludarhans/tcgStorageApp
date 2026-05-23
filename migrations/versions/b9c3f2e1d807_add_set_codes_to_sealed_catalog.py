"""add set_codes to sealed_catalog

Revision ID: b9c3f2e1d807
Revises: a4e61f699bd4
Create Date: 2026-05-22
"""
from alembic import op
import sqlalchemy as sa

revision = 'b9c3f2e1d807'
down_revision = 'a4e61f699bd4'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('sealed_catalog',
        sa.Column('set_codes', sa.Text(), nullable=True)
    )
    # Backfill: set_codes = ",{set_code},"  for all existing rows
    op.execute(
        "UPDATE sealed_catalog SET set_codes = ',' || set_code || ',' WHERE set_code IS NOT NULL"
    )


def downgrade():
    op.drop_column('sealed_catalog', 'set_codes')
