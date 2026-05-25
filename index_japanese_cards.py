#!/usr/bin/env python3
"""
Index Japanese Pokémon card data into the local CardCatalog database.

Data is fetched from TCGdex (https://api.tcgdex.net/v2/ja/) — a free,
open community API that supports the full Japanese card catalog.

Usage:
    python3 index_japanese_cards.py              # index all sets in ALL_SETS_JA
    python3 index_japanese_cards.py --sets SV1S SV1V SV3
    python3 index_japanese_cards.py --reset      # clear JA cards first, then re-index
    python3 index_japanese_cards.py --details    # also fetch per-card rarity/HP (slower)
    python3 index_japanese_cards.py --list-sets  # print every TCGdex JP set code and exit

Cards are stored in CardCatalog with era='ja-sv' / 'ja-swsh' / etc. so they
never collide with English cards (era='sv', 'swsh', etc.).
JA tcg_id values are prefixed 'ja-' (e.g. 'ja-SV1S-001').
"""

import sys
import os
import time
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import requests

from app import app, db
from app.models import CardCatalog
from app.forms import ALL_SETS_JA

# ── TCGdex Japanese API ───────────────────────────────────────────────────────
API_BASE = "https://api.tcgdex.net/v2/ja"

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "CardStorage/1.0 (personal collection tracker)",
    "Accept":     "application/json",
})


# ── Era tag based on set-code prefix ─────────────────────────────────────────
def era_for(code: str) -> str:
    c = code.upper()
    if c.startswith("SV"):   return "ja-sv"
    if c.startswith("SM"):   return "ja-sm"
    if c.startswith("GG"):   return "ja-sm"
    if c.startswith("S"):    return "ja-swsh"
    if c.startswith("XY"):   return "ja-xy"
    if c.startswith("CP"):   return "ja-xy"
    if "-P" in c:            return "ja-promo"
    return "ja"


# ── API helpers ───────────────────────────────────────────────────────────────
def api_get(path: str, timeout: int = 15):
    """GET from TCGdex; returns parsed JSON or None on 404/error."""
    try:
        r = SESSION.get(f"{API_BASE}/{path}", timeout=timeout)
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        print(f"    ✕ GET {path}: {e}")
        return None


# ── Set indexing ──────────────────────────────────────────────────────────────
def index_set(set_code: str, set_name: str, fetch_details: bool = False) -> int:
    """Fetch all cards for set_code from TCGdex and upsert into CardCatalog."""
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
            card_id  = card.get("id", "")          # e.g. "SV1S-001"
            local_id = str(card.get("localId", "")).strip()  # e.g. "001"
            name     = (card.get("name") or "").strip()
            img_base = card.get("image", "")        # base URL without extension

            if not name:
                skipped += 1
                continue

            # Unique ID — ja- prefix prevents collision with EN catalog
            tcg_id = (
                f"ja-{card_id}" if card_id
                else f"ja-{set_code}-{local_id or name[:20]}"
            )

            if CardCatalog.query.filter_by(tcg_id=tcg_id).first():
                skipped += 1
                continue

            # Image URL: TCGdex serves <base>/high.jpg
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
                time.sleep(0.08)   # be polite to the API

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


# ── --list-sets helper ────────────────────────────────────────────────────────
def cmd_list_sets():
    print("Fetching all Japanese sets from TCGdex …\n")
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


# ── CLI ───────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Index Japanese Pokémon TCG cards into the local catalog.",
    )
    parser.add_argument(
        "--sets", nargs="*", metavar="CODE",
        help="Only index these set codes (e.g. SV1S SV1V SV3)",
    )
    parser.add_argument(
        "--reset", action="store_true",
        help="Delete all existing JA catalog entries before re-indexing",
    )
    parser.add_argument(
        "--details", action="store_true",
        help="Fetch individual card details for rarity/HP (slower but complete)",
    )
    parser.add_argument(
        "--list-sets", action="store_true",
        help="Print all TCGdex Japanese set codes and exit",
    )
    args = parser.parse_args()

    if args.list_sets:
        cmd_list_sets()
        return

    # ── Determine which sets to process ──────────────────────────────────────
    if args.sets:
        wanted = {c.upper() for c in args.sets}
        sets_to_index = [
            (code, name) for code, name in ALL_SETS_JA
            if code.upper() in wanted
        ]
        missing = wanted - {c.upper() for c, _ in sets_to_index}
        if missing:
            print(f"Warning: not in ALL_SETS_JA: {', '.join(sorted(missing))}")
            print("Tip: use --list-sets to browse TCGdex codes; add new ones to forms.py")
        if not sets_to_index:
            print("No matching sets found. Valid codes in ALL_SETS_JA:")
            for code, name in ALL_SETS_JA:
                print(f"  {code:<12}  {name}")
            sys.exit(1)
    else:
        sets_to_index = ALL_SETS_JA

    # ── Optional reset ────────────────────────────────────────────────────────
    with app.app_context():
        if args.reset:
            deleted = (
                CardCatalog.query
                .filter(CardCatalog.era.like("ja-%"))
                .delete(synchronize_session=False)
            )
            db.session.commit()
            print(f"Cleared {deleted} existing Japanese card entries.\n")

        existing = (
            CardCatalog.query
            .filter(CardCatalog.era.like("ja-%"))
            .count()
        )
        if existing:
            print(f"({existing} Japanese cards already in catalog)\n")

    # ── Index ─────────────────────────────────────────────────────────────────
    print(f"Indexing {len(sets_to_index)} Japanese set(s) …")
    if args.details:
        print("(--details mode: fetching individual card details for rarity/HP)\n")

    total  = 0
    failed = []

    for code, name in sets_to_index:
        # Strip year suffix for storage: "Scarlet ex (2022)" → "Scarlet ex"
        clean = name.rsplit(" (", 1)[0].strip()
        try:
            total += index_set(code, clean, fetch_details=args.details)
        except Exception as e:
            print(f"  ✕ {code} failed: {e}")
            failed.append(code)
        time.sleep(0.3)   # polite gap between sets

    # ── Summary ───────────────────────────────────────────────────────────────
    print(f"\n{'─'*50}")
    print(f"Done.  Total cards added: {total}")
    if failed:
        print(f"Failed sets ({len(failed)}): {', '.join(failed)}")
        print("Retry with:")
        print(f"  python3 index_japanese_cards.py --sets {' '.join(failed)}")


if __name__ == "__main__":
    main()
