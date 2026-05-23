"""
Fetch TCGPlayer market prices for every item in the sealed_catalog table
and cache them as SealedCatalog.market_price.

Requires a free TCGPlayer Partner API key — register at:
    https://developer.tcgplayer.com

Then add these two lines to your .flaskenv:
    TCGPLAYER_PUBLIC_KEY=your-public-key
    TCGPLAYER_PRIVATE_KEY=your-private-key

Usage:
    python fetch_sealed_prices.py           # only rows that have no price yet
    python fetch_sealed_prices.py --all     # refresh every row
    python fetch_sealed_prices.py --dry-run # print matches without saving
"""

import os
import sys
import time

import requests

os.environ.setdefault('FLASK_APP', 'main.py')
os.environ.setdefault('SECRET_KEY', 'price-fetch')

from app import app, db
from app.models import SealedCatalog

# ── TCGPlayer OAuth endpoints ─────────────────────────────────────────────────
TOKEN_URL   = 'https://api.tcgplayer.com/token'
SEARCH_URL  = 'https://api.tcgplayer.com/v1.39.0/catalog/products'
PRICING_URL = 'https://api.tcgplayer.com/v1.39.0/pricing/product/{}'

POKEMON_LINE_ID = 3   # TCGPlayer category ID for Pokémon TCG


# ── TCGPlayer item-type → productTypeName mapping ────────────────────────────
TYPE_MAP = {
    'Booster Pack':             'Booster Pack',
    'Blister Pack':             'Blister Pack',
    'Booster Box':              'Booster Box',
    'Elite Trainer Box':        'Elite Trainer Box',
    'Super Premium Collection': 'Premium Collection Box',
    'Premium Collection':       'Premium Collection Box',
    'Collection Box':           'Collection Box',
    'Tin':                      'Tin',
    'Bundle':                   'Bundle',
    'Gift Box':                 'Gift Set',
    'Other':                    '',
}


def get_token(pub_key: str, priv_key: str) -> str:
    resp = requests.post(
        TOKEN_URL,
        data={
            'grant_type':    'client_credentials',
            'client_id':     pub_key,
            'client_secret': priv_key,
        },
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()['access_token']


def search_product(name: str, item_type: str, headers: dict) -> int | None:
    """Return the best-matching TCGPlayer productId, or None."""
    params = {
        'productLineName': 'Pokemon',
        'productName':     name,
        'limit':           10,
        'offset':          0,
    }
    tcg_type = TYPE_MAP.get(item_type, '')
    if tcg_type:
        params['productTypeName'] = tcg_type

    try:
        r = requests.get(SEARCH_URL, params=params, headers=headers, timeout=10)
        r.raise_for_status()
        results = r.json().get('results', [])
    except Exception as exc:
        print(f'    search error: {exc}')
        return None

    if not results:
        return None

    # Prefer exact name match first
    for p in results:
        if p.get('name', '').lower() == name.lower():
            return p['productId']

    # Fall back to first result
    return results[0]['productId']


def fetch_price(product_id: int, headers: dict) -> float | None:
    """Return the market price for a TCGPlayer productId, or None."""
    try:
        r = requests.get(
            PRICING_URL.format(product_id),
            headers=headers,
            timeout=10,
        )
        r.raise_for_status()
        results = r.json().get('results', [])
    except Exception as exc:
        print(f'    pricing error: {exc}')
        return None

    # Each result has a subTypeName (e.g. "Normal", "1st Edition")
    # and marketPrice / midPrice / lowPrice / highPrice.
    # Take the best (non-zero) market price.
    for row in results:
        mp = row.get('marketPrice')
        if mp and float(mp) > 0:
            return float(mp)

    # Fall back to midPrice
    for row in results:
        mp = row.get('midPrice')
        if mp and float(mp) > 0:
            return float(mp)

    return None


def run(refresh_all: bool = False, dry_run: bool = False) -> None:
    pub_key  = os.environ.get('TCGPLAYER_PUBLIC_KEY',  '').strip()
    priv_key = os.environ.get('TCGPLAYER_PRIVATE_KEY', '').strip()

    if not pub_key or not priv_key:
        print(
            '\n  No TCGPlayer API keys found.\n'
            '  Register for free at https://developer.tcgplayer.com,\n'
            '  then add to .flaskenv:\n'
            '      TCGPLAYER_PUBLIC_KEY=your-public-key\n'
            '      TCGPLAYER_PRIVATE_KEY=your-private-key\n'
        )
        sys.exit(1)

    print('Authenticating with TCGPlayer …')
    try:
        token = get_token(pub_key, priv_key)
    except Exception as exc:
        print(f'  Auth failed: {exc}')
        sys.exit(1)

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type':  'application/json',
    }
    print('  OK\n')

    with app.app_context():
        query = SealedCatalog.query
        if not refresh_all:
            query = query.filter(SealedCatalog.market_price.is_(None))

        rows = query.order_by(SealedCatalog.item_type, SealedCatalog.name).all()
        total = len(rows)
        print(f'{total} catalog entries to process.\n')

        updated = skipped = errors = 0

        for i, row in enumerate(rows, 1):
            label = f'[{i:4d}/{total}] {row.item_type:25s}  {row.name}'
            print(label, end=' … ', flush=True)

            pid = search_product(row.name, row.item_type, headers)
            if pid is None:
                print('no match')
                skipped += 1
                time.sleep(0.15)
                continue

            price = fetch_price(pid, headers)
            if price is None:
                print(f'pid={pid} — no price')
                skipped += 1
                time.sleep(0.15)
                continue

            print(f'${price:.2f}  (pid={pid})')

            if not dry_run:
                from datetime import datetime
                row.market_price      = price
                row.last_price_update = datetime.utcnow()
                updated += 1

            time.sleep(0.15)  # be polite

        if not dry_run:
            db.session.commit()

        print(f'\nDone.  updated={updated}  skipped/no-match={skipped}  errors={errors}')
        print(f'Sealed catalog total with prices: '
              f'{SealedCatalog.query.filter(SealedCatalog.market_price.isnot(None)).count()} / '
              f'{SealedCatalog.query.count()}')


if __name__ == '__main__':
    refresh_all = '--all'     in sys.argv
    dry_run     = '--dry-run' in sys.argv

    with app.app_context():
        run(refresh_all=refresh_all, dry_run=dry_run)
