"""Add market_price + last_price_update to sealed_catalog;
   add last_price_update to sealed_items.

Revision ID: d3f1a9e4c820
Revises: c1d4e7f2a903
Create Date: 2026-05-23
"""
from alembic import op
import sqlalchemy as sa

revision = 'd3f1a9e4c820'
down_revision = 'c1d4e7f2a903'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('sealed_catalog', schema=None) as batch_op:
        batch_op.add_column(sa.Column('market_price',      sa.Float(),    nullable=True))
        batch_op.add_column(sa.Column('last_price_update', sa.DateTime(), nullable=True))

    with op.batch_alter_table('sealed_items', schema=None) as batch_op:
        batch_op.add_column(sa.Column('last_price_update', sa.DateTime(), nullable=True))


def downgrade():
    with op.batch_alter_table('sealed_items', schema=None) as batch_op:
        batch_op.drop_column('last_price_update')

    with op.batch_alter_table('sealed_catalog', schema=None) as batch_op:
        batch_op.drop_column('last_price_update')
        batch_op.drop_column('market_price')
