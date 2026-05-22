"""
Fetch every card for every set in ALL_SETS from the Pokemon TCG API
and upsert them into the local card_catalog table.

Usage:
    python index_cards.py              # index all sets
    python index_cards.py sv1 sv2      # index specific set codes only
    python index_cards.py --refresh    # re-index even if a set is already indexed

Set an API key in .flaskenv to avoid the free-tier rate limit:
    POKEMON_TCG_API_KEY=your-key-here
"""
import os
import sys
import math
import time
import requests

os.environ.setdefault('SQLITE_DB', 'pokemon.db')
os.environ.setdefault('SECRET_KEY', 'index-seed')

from app import app, db
from app.models import CardCatalog
from app.forms import ALL_SETS

API_BASE   = 'https://api.pokemontcg.io/v2/cards'
PAGE_SIZE  = 250
FIELDS     = 'id,name,number,rarity,supertype,types,hp,images,set,tcgplayer'


def era_for(set_code: str) -> str:
    if set_code.startswith('xy'):
        return 'xy'
    if set_code.startswith('sm'):
        return 'sm'
    if set_code.startswith('swsh') or set_code in ('cel25', 'pgo'):
        return 'swsh'
    if set_code.startswith('sv'):
        return 'sv'
    return 'other'


def best_price(tcgplayer: dict | None) -> float | None:
    if not tcgplayer:
        return None
    prices = tcgplayer.get('prices') or {}
    order = ['holofoil', 'reverseHolofoil', 'normal',
             '1stEditionHolofoil', 'unlimitedHolofoil']
    for key in order:
        m = prices.get(key, {}).get('market')
        if m:
            return m
    for p in prices.values():
        m = p.get('market')
        if m:
            return m
    return None


def fetch_set(set_code: str, headers: dict) -> list[dict]:
    """Return all raw card dicts for one set."""
    cards = []
    page  = 1
    total = None
    while True:
        resp = requests.get(
            API_BASE,
            params={
                'q':        f'set.id:{set_code}',
                'page':     page,
                'pageSize': PAGE_SIZE,
                'select':   FIELDS,
            },
            headers=headers,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        cards.extend(data.get('data', []))
        if total is None:
            total = data.get('totalCount', 0)
        if len(cards) >= total:
            break
        page += 1
        time.sleep(0.3)  # be polite even with an API key
    return cards


def upsert_card(raw: dict) -> None:
    tcg_id = raw['id']
    obj = CardCatalog.query.filter_by(tcg_id=tcg_id).first()
    if obj is None:
        obj = CardCatalog(tcg_id=tcg_id)

    obj.name        = raw.get('name', '')
    obj.card_number = raw.get('number', '')
    obj.set_code    = raw.get('set', {}).get('id', '')
    obj.set_name    = raw.get('set', {}).get('name', '')
    obj.era         = era_for(obj.set_code)
    obj.rarity      = raw.get('rarity', '')
    obj.supertype   = raw.get('supertype', '')
    obj.types       = ','.join(raw.get('types') or [])
    hp_raw          = raw.get('hp')
    obj.hp          = int(hp_raw) if hp_raw and str(hp_raw).isdigit() else None
    obj.image_small = (raw.get('images') or {}).get('small', '')
    obj.image_large = (raw.get('images') or {}).get('large', '')
    obj.market_price = best_price(raw.get('tcgplayer'))
    db.session.add(obj)


def main():
    api_key = os.environ.get('POKEMON_TCG_API_KEY', '')
    headers = {'X-Api-Key': api_key} if api_key else {}
    if api_key:
        print('Using API key — no rate limits.')
    else:
        print('No API key — running on free tier (1 000 req/day).')

    # Decide which sets to process
    refresh   = '--refresh' in sys.argv
    cli_codes = [a for a in sys.argv[1:] if not a.startswith('--')]

    if cli_codes:
        valid = {code for code, _ in ALL_SETS}
        unknown = [c for c in cli_codes if c not in valid]
        if unknown:
            print(f'Unknown set codes: {unknown}')
            sys.exit(1)
        targets = [(code, label) for code, label in ALL_SETS if code in cli_codes]
    else:
        targets = list(ALL_SETS)

    # Skip already-indexed sets unless --refresh
    if not refresh:
        indexed = set(
            r[0] for r in db.session.query(CardCatalog.set_code).distinct()
        )
        targets = [(c, l) for c, l in targets if c not in indexed]
        if not targets:
            total = CardCatalog.query.count()
            print(f'All sets already indexed ({total:,} cards). Use --refresh to re-index.')
            return

    print(f'Sets to index: {len(targets)}')
    total_indexed = 0

    for i, (set_code, set_label) in enumerate(targets, 1):
        print(f'  [{i:2d}/{len(targets)}] {set_code:12s}  {set_label} …', end=' ', flush=True)
        try:
            cards = fetch_set(set_code, headers)
            for card in cards:
                upsert_card(card)
            db.session.commit()
            total_indexed += len(cards)
            print(f'{len(cards)} cards')
        except Exception as exc:
            db.session.rollback()
            print(f'FAILED ({exc})')

    print(f'\nDone. {total_indexed:,} cards indexed.')
    print(f'Catalog total: {CardCatalog.query.count():,} cards.')


if __name__ == '__main__':
    with app.app_context():
        main()
