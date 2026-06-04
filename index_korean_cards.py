#!/usr/bin/env python3
"""
Index Korean Pokémon card data into the local CardCatalog database.

Data is fetched from TCGdex (https://api.tcgdex.net/v2/ko/) — a free,
open community API that supports Korean card data.

Usage:
    python3 index_korean_cards.py              # index all sets in ALL_SETS_KO
    python3 index_korean_cards.py --sets SV4K SV5K
    python3 index_korean_cards.py --reset      # clear KO cards first, then re-index
    python3 index_korean_cards.py --details    # also fetch per-card rarity/HP (slower)
    python3 index_korean_cards.py --list-sets  # print every TCGdex KO set code and exit

Cards are stored in CardCatalog with era='ko-sv' / 'ko-swsh' / etc. so they
never collide with English or Japanese cards.
KO tcg_id values are prefixed 'ko-' (e.g. 'ko-SV4K-001').
"""

import sys
import os
import time
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import requests

from app import app, db
from app.models import CardCatalog
from app.forms import ALL_SETS_KO

API_BASE = "https://api.tcgdex.net/v2/ko"

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "CardStorage/1.0 (personal collection tracker)",
    "Accept":     "application/json",
})


def era_for(code: str) -> str:
    c = code.upper()
    if c.startswith("SV"):                    return "ko-sv"
    if c.startswith("SM") or c.startswith("SN"): return "ko-sm"
    if c.startswith("S"):                     return "ko-swsh"
    if "-P" in c:                             return "ko-promo"
    return "ko"


def api_get(path: str, timeout: int = 15):
    try:
        r = SESSION.get(f"{API_BASE}/{path}", timeout=timeout)
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        print(f"    ✕ GET {path}: {e}")
        return None


def index_set(set_code: str, set_name: str, fetch_details: bool = False) -> int:
    print(f"\n  [{set_code}] {set_name}")

    data = api_get(f"sets/{set_code}")
    if data is None:
        print(f"  → Not found in TCGdex (check set code)")
        return 0

    cards = data.get("cards", [])
    if not cards:
        print(f"  → No cards in TCGdex response")
        return 0

    print(f"    {len(cards)} cards found")
    added = skipped = 0

    with app.app_context():
        for card in cards:
            card_id  = card.get("id", "")
            local_id = str(card.get("localId", "")).strip()
            name     = (card.get("name") or "").strip()
            img_base = card.get("image", "")

            if not name:
                skipped += 1
                continue

            tcg_id = (
                f"ko-{card_id}" if card_id
                else f"ko-{set_code}-{local_id or name[:20]}"
            )

            if CardCatalog.query.filter_by(tcg_id=tcg_id).first():
                skipped += 1
                continue

            img = f"{img_base}/high.jpg" if img_base else ""

            rarity    = None
            supertype = "Pokémon"

            if fetch_details and card_id:
                detail = api_get(f"cards/{card_id}")
                if detail:
                    rarity    = detail.get("rarity") or None
                    cat       = (detail.get("category")
                                 or detail.get("supertype")
                                 or "Pokémon")
                    supertype = cat
                time.sleep(0.08)

            db.session.add(CardCatalog(
                tcg_id      = tcg_id,
                name        = name,
                card_number = local_id or None,
                set_name    = set_name,
                set_code    = set_code,
                era         = era_for(set_code),
                rarity      = rarity,
                supertype   = supertype,
                image_small = img,
                image_large = img,
            ))
            added += 1

        db.session.commit()

    print(f"  → Added {added}  |  Skipped (already exists) {skipped}")
    return added


def cmd_list_sets():
    print("Fetching all Korean sets from TCGdex …\n")
    sets = api_get("sets")
    if not sets:
        print("Failed to retrieve set list.")
        return
    if isinstance(sets, list):
        print(f"  {'Code':<14} Name")
        print(f"  {'-'*14} {'-'*40}")
        for s in sorted(sets, key=lambda x: x.get("id", "")):
            code = s.get("id", "?")
            name = s.get("name", "?")
            print(f"  {code:<14} {name}")
        print(f"\n{len(sets)} sets total.")
    else:
        print(sets)


def main():
    parser = argparse.ArgumentParser(
        description="Index Korean Pokémon TCG cards into the local catalog.",
    )
    parser.add_argument("--sets", nargs="*", metavar="CODE")
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--details", action="store_true")
    parser.add_argument("--list-sets", action="store_true")
    args = parser.parse_args()

    if args.list_sets:
        cmd_list_sets()
        return

    if args.sets:
        wanted = {c.upper() for c in args.sets}
        sets_to_index = [
            (code, name) for code, name in ALL_SETS_KO
            if code.upper() in wanted
        ]
        missing = wanted - {c.upper() for c, _ in sets_to_index}
        if missing:
            print(f"Warning: not in ALL_SETS_KO: {', '.join(sorted(missing))}")
        if not sets_to_index:
            print("No matching sets found.")
            sys.exit(1)
    else:
        sets_to_index = ALL_SETS_KO

    with app.app_context():
        if args.reset:
            deleted = (
                CardCatalog.query
                .filter(CardCatalog.era.like("ko-%"))
                .delete(synchronize_session=False)
            )
            db.session.commit()
            print(f"Cleared {deleted} existing Korean card entries.\n")

        existing = (
            CardCatalog.query
            .filter(CardCatalog.era.like("ko-%"))
            .count()
        )
        if existing:
            print(f"({existing} Korean cards already in catalog)\n")

    print(f"Indexing {len(sets_to_index)} Korean set(s) …")
    if args.details:
        print("(--details mode: fetching individual card details for rarity/HP)\n")

    total  = 0
    failed = []

    for code, name in sets_to_index:
        clean = name.rsplit(" (", 1)[0].strip()
        try:
            total += index_set(code, clean, fetch_details=args.details)
        except Exception as e:
            print(f"  ✕ {code} failed: {e}")
            failed.append(code)
        time.sleep(0.3)

    print(f"\n{'─'*50}")
    print(f"Done.  Total cards added: {total}")
    if failed:
        print(f"Failed sets ({len(failed)}): {', '.join(failed)}")
        print(f"Retry with: python3 index_korean_cards.py --sets {' '.join(failed)}")


if __name__ == "__main__":
    main()
