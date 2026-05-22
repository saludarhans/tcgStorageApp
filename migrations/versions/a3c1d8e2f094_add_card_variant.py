"""add card variant

Revision ID: a3c1d8e2f094
Revises: f8548b29851f
Create Date: 2026-05-22

"""
from alembic import op
import sqlalchemy as sa


revision = 'a3c1d8e2f094'
down_revision = 'f8548b29851f'
branch_labels = None
depends_on = None


def detect_variant(name, rarity, is_foil):
    """Infer a card's visual/print variant from its name, rarity, and foil flag."""
    r = (rarity or '').lower()
    n = (name or '').lower()

    if 'special illustration rare' in r: return 'Special Illustration Rare'
    if 'illustration rare'         in r: return 'Illustration Rare'
    if 'hyper rare'                in r: return 'Gold'
    if 'rare rainbow' in r or 'rainbow rare' in r: return 'Rainbow Rare'
    if 'rare secret'  in r or 'secret rare'  in r: return 'Secret Rare'
    if 'rare ultra'   in r:              return 'Full Art'
    if 'amazing rare' in r:              return 'Amazing Rare'
    if 'prism star'   in r:              return 'Prism Star'
    if 'rare break'   in r or n.endswith(' break'): return 'BREAK'

    # Name-based (more reliable for mechanical subtypes)
    if 'vmax' in n: return 'VMax'
    if 'vstar' in n: return 'VStar'
    if n.endswith('-gx') or n.endswith(' gx') or 'rare holo gx' in r or 'shiny gx' in r:
        return 'GX'
    if n.endswith('-ex') or n.endswith(' ex') or 'holo ex' in r:
        return 'EX'
    if ('rare holo v' in r and 'vmax' not in r and 'vstar' not in r) or \
       (n.endswith(' v') and 'vmax' not in n and 'vstar' not in n):
        return 'V'

    if 'reverse holo' in r:           return 'Reverse Holo'
    if 'holo' in r or bool(is_foil):  return 'Holo'
    return 'Special'


def upgrade():
    op.add_column('cards', sa.Column('variant', sa.String(60), nullable=True))

    conn = op.get_bind()
    rows = conn.execute(sa.text('SELECT id, name, rarity, is_foil FROM cards')).fetchall()
    for row in rows:
        v = detect_variant(row[1], row[2], row[3])
        conn.execute(
            sa.text('UPDATE cards SET variant = :v WHERE id = :id'),
            {'v': v, 'id': row[0]}
        )


def downgrade():
    op.drop_column('cards', 'variant')
