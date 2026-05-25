"""
Seed ALL basic energy cards into the card_catalog table.

Fetches every card matching supertype:Energy subtypes:Basic from the
Pokemon TCG API (paginated) and upserts each one into the local
card_catalog, tagged with the correct era derived from its set code.

This means every set that has its own energy art (e.g. each SV set with
unique energy artwork) gets its own entries — so users see the right
version when ripping or browsing that specific set.

Usage:
    python seed_energies.py              # skip cards already present
    python seed_energies.py --refresh    # re-fetch and overwrite all
"""

import os, sys, time
import requests

os.environ.setdefault('FLASK_APP', 'main.py')
os.environ.setdefault('SECRET_KEY', 'seed-energies')

from app import app, db
from app.models import CardCatalog

API_BASE = 'https://api.pokemontcg.io/v2/cards'
PAGE_SIZE = 250   # maximum the API allows


def _era_for(code: str) -> str:
    """Mirror of the same helper in routes.py."""
    if not code:
        return 'other'
    if code in ('svp', 'swshp', 'smp', 'xyp', 'bwp'):
        return 'promo'
    if code.startswith('me'):
        return 'me'
    if code.startswith('swsh') or code in ('cel25', 'pgo'):
        return 'swsh'
    if code.startswith('sv') or code.startswith('rsv') or code.startswith('zsv'):
        return 'sv'
    if code.startswith('sm'):
        return 'sm'
    if code.startswith('xy'):
        return 'xy'
    return 'other'


def fetch_all_energies(headers: dict) -> list[dict]:
    """Paginate through the TCG API and return every basic Energy card."""
    all_cards = []
    page = 1
    while True:
        params = {
            'q':        'supertype:Energy subtypes:Basic',
            'pageSize': PAGE_SIZE,
            'page':     page,
            'select':   'id,name,number,rarity,supertype,subtypes,images,set',
        }
        r = requests.get(API_BASE, params=params, headers=headers, timeout=20)
        r.raise_for_status()
        body  = r.json()
        cards = body.get('data', [])
        all_cards.extend(cards)
        total = body.get('totalCount', 0)
        print(f'    page {page}: {len(cards)} cards  (total so far: {len(all_cards)} / {total})')
        if len(all_cards) >= total or not cards:
            break
        page += 1
        time.sleep(0.2)   # be polite to the API
    return all_cards


def upsert(raw: dict) -> bool:
    """Insert or update one CardCatalog row. Returns True if newly created."""
    tcg_id = raw['id']
    set_id = raw.get('set', {}).get('id', '')
    era    = _era_for(set_id)

    obj    = CardCatalog.query.filter_by(tcg_id=tcg_id).first()
    is_new = obj is None
    if is_new:
        obj = CardCatalog(tcg_id=tcg_id)

    obj.name        = raw.get('name', '')
    obj.card_number = raw.get('number', '')
    obj.set_code    = set_id
    obj.set_name    = raw.get('set', {}).get('name', '')
    obj.era         = era
    obj.rarity      = raw.get('rarity', 'Energy')
    obj.supertype   = raw.get('supertype', 'Energy')
    obj.types       = ''      # basic energies have no Pokémon type column
    obj.hp          = None
    obj.image_small = raw.get('images', {}).get('small', '')
    obj.image_large = raw.get('images', {}).get(
        'large', raw.get('images', {}).get('small', ''))

    db.session.add(obj)
    return is_new


def main():
    refresh = '--refresh' in sys.argv
    api_key = os.environ.get('POKEMON_TCG_API_KEY', '').strip()
    headers = {'X-Api-Key': api_key} if api_key else {}

    print('Seeding ALL basic energy cards into card_catalog…')
    if api_key:
        print('  API key found — higher rate limit.')
    else:
        print('  No API key — free tier (1 000 req/day, slower).')

    if not refresh:
        existing = CardCatalog.query.filter_by(supertype='Energy').count()
        if existing:
            print(f'\n  {existing} energy cards already present.')
            print('  Run with --refresh to re-fetch and overwrite.')
            print(f'\nDone. No new cards added.')
            return

    print()

    with app.app_context():
        try:
            print('  Fetching from TCG API…')
            cards = fetch_all_energies(headers)
            print(f'\n  Fetched {len(cards)} energy cards total. Upserting…')

            new_count = 0
            for i, card in enumerate(cards, 1):
                if upsert(card):
                    new_count += 1
                if i % 100 == 0:
                    db.session.commit()
                    print(f'    …committed {i}/{len(cards)}')

            db.session.commit()
            print(f'\n  Done. {new_count} new, {len(cards) - new_count} updated.')

        except Exception as exc:
            db.session.rollback()
            print(f'\nFAILED — {exc}')
            raise

    with app.app_context():
        total = CardCatalog.query.filter_by(supertype='Energy').count()
        era_counts = db.session.execute(
            db.text("SELECT era, COUNT(*) FROM card_catalog WHERE supertype='Energy' GROUP BY era ORDER BY era")
        ).fetchall()
        print(f'\nTotal energy cards in catalog: {total}')
        for era, count in era_counts:
            print(f'  {era:8s}  {count}')


if __name__ == '__main__':
    main()
