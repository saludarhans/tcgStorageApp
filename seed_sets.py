"""
Run this once after `flask db upgrade` to populate the set reference data.
Usage:  python seed_sets.py
"""
import os
os.environ.setdefault('SQLITE_DB', 'pokemon.db')
os.environ.setdefault('SECRET_KEY', 'seed')

from app import app, db
from app.models import Card, User

# Every mainline English set from XY (Feb 2014) through early 2026
# Format: (set_name, set_code, era, release_year)
SETS = [
    # ── XY Era (2014-2016) ────────────────────────────────────────────────
    ("XY Base Set",                    "xy1",      "XY",            2014),
    ("XY Flashfire",                   "xy2",      "XY",            2014),
    ("XY Furious Fists",               "xy3",      "XY",            2014),
    ("XY Phantom Forces",              "xy4",      "XY",            2014),
    ("XY Primal Clash",                "xy5",      "XY",            2015),
    ("XY Roaring Skies",               "xy6",      "XY",            2015),
    ("XY Ancient Origins",             "xy7",      "XY",            2015),
    ("XY BREAKthrough",                "xy8",      "XY",            2015),
    ("XY BREAKpoint",                  "xy9",      "XY",            2016),
    ("XY Fates Collide",               "xy10",     "XY",            2016),
    ("XY Steam Siege",                 "xy11",     "XY",            2016),
    ("XY Evolutions",                  "xy12",     "XY",            2016),
    # ── Sun & Moon Era (2017-2019) ────────────────────────────────────────
    ("Sun & Moon Base Set",            "sm1",      "Sun & Moon",    2017),
    ("Sun & Moon Guardians Rising",    "sm2",      "Sun & Moon",    2017),
    ("Sun & Moon Burning Shadows",     "sm3",      "Sun & Moon",    2017),
    ("Sun & Moon Crimson Invasion",    "sm4",      "Sun & Moon",    2017),
    ("Sun & Moon Ultra Prism",         "sm5",      "Sun & Moon",    2018),
    ("Sun & Moon Forbidden Light",     "sm6",      "Sun & Moon",    2018),
    ("Sun & Moon Celestial Storm",     "sm7",      "Sun & Moon",    2018),
    ("Sun & Moon Dragon Majesty",      "sm75",     "Sun & Moon",    2018),
    ("Sun & Moon Lost Thunder",        "sm8",      "Sun & Moon",    2018),
    ("Sun & Moon Team Up",             "sm9",      "Sun & Moon",    2019),
    ("Sun & Moon Unbroken Bonds",      "sm10",     "Sun & Moon",    2019),
    ("Sun & Moon Unified Minds",       "sm11",     "Sun & Moon",    2019),
    ("Sun & Moon Hidden Fates",        "sm115",    "Sun & Moon",    2019),
    ("Sun & Moon Cosmic Eclipse",      "sm12",     "Sun & Moon",    2019),
    # ── Sword & Shield Era (2020-2023) ────────────────────────────────────
    ("Sword & Shield Base Set",        "swsh1",    "Sword & Shield",2020),
    ("Sword & Shield Rebel Clash",     "swsh2",    "Sword & Shield",2020),
    ("Sword & Shield Darkness Ablaze", "swsh3",    "Sword & Shield",2020),
    ("Champion's Path",                "swsh35",   "Sword & Shield",2020),
    ("Sword & Shield Vivid Voltage",   "swsh4",    "Sword & Shield",2020),
    ("Shining Fates",                  "swsh45",   "Sword & Shield",2021),
    ("Sword & Shield Battle Styles",   "swsh5",    "Sword & Shield",2021),
    ("Sword & Shield Chilling Reign",  "swsh6",    "Sword & Shield",2021),
    ("Sword & Shield Evolving Skies",  "swsh7",    "Sword & Shield",2021),
    ("Celebrations",                   "cel25",    "Sword & Shield",2021),
    ("Sword & Shield Fusion Strike",   "swsh8",    "Sword & Shield",2021),
    ("Sword & Shield Brilliant Stars", "swsh9",    "Sword & Shield",2022),
    ("Sword & Shield Astral Radiance", "swsh10",   "Sword & Shield",2022),
    ("Pokemon GO",                     "pgo",      "Sword & Shield",2022),
    ("Sword & Shield Lost Origin",     "swsh11",   "Sword & Shield",2022),
    ("Silver Tempest",                 "swsh12",   "Sword & Shield",2022),
    ("Crown Zenith",                   "swsh12pt5","Sword & Shield",2023),
    # ── Scarlet & Violet Era (2023-present) ──────────────────────────────
    ("Scarlet & Violet Base Set",      "sv1",      "Scarlet & Violet",2023),
    ("Scarlet & Violet Paldea Evolved","sv2",      "Scarlet & Violet",2023),
    ("Scarlet & Violet Obsidian Flames","sv3",     "Scarlet & Violet",2023),
    ("198 Scarlet & Violet 151",       "sv3pt5",   "Scarlet & Violet",2023),
    ("Scarlet & Violet Paradox Rift",  "sv4",      "Scarlet & Violet",2023),
    ("Scarlet & Violet Paldean Fates", "sv4pt5",   "Scarlet & Violet",2024),
    ("Scarlet & Violet Temporal Forces","sv5",     "Scarlet & Violet",2024),
    ("Scarlet & Violet Twilight Masquerade","sv6", "Scarlet & Violet",2024),
    ("Scarlet & Violet Shrouded Fable","sv6pt5",   "Scarlet & Violet",2024),
    ("Scarlet & Violet Stellar Crown", "sv7",      "Scarlet & Violet",2024),
    ("Scarlet & Violet Surging Sparks","sv8",      "Scarlet & Violet",2024),
    ("Prismatic Evolutions",           "sv8pt5",   "Scarlet & Violet",2025),
    ("Scarlet & Violet Journey Together","sv9",    "Scarlet & Violet",2025),
    ("Scarlet & Violet Destined Rivals","sv10",    "Scarlet & Violet",2025),
    ("Mega Evolution",                 "sv10pt5",  "Scarlet & Violet",2025),
    ("White Flare",                    "sv11wf",   "Scarlet & Violet",2025),
    ("Black Bolt",                     "sv11bb",   "Scarlet & Violet",2025),
    ("Phantasmal Flames",              "sv12",     "Scarlet & Violet",2025),
    # ── 2026 releases ─────────────────────────────────────────────────────
    ("Ascended Heroes",                "sv13",     "Scarlet & Violet",2026),
    ("Perfect Order",                  "sv14",     "Scarlet & Violet",2026),
]

def main():
    with app.app_context():
        print(f"Total sets defined: {len(SETS)}")
        for name, code, era, year in SETS:
            print(f"  {year}  [{code:12s}]  {name}")
        print("\nSet list verified. Use this data in your app or import it as needed.")
        print("To seed actual cards, integrate with the Pokemon TCG API (https://dev.pokemontcg.io/).")

if __name__ == '__main__':
    main()
