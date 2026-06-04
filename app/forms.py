import re
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (StringField, PasswordField, BooleanField, SubmitField,
                     SelectField, IntegerField, FloatField, TextAreaField)
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, NumberRange

_ERA_PREFIXES = ('Scarlet & Violet ', 'Sword & Shield ', 'Sun & Moon ', 'XY ')

def shorten_set_name(full: str) -> str:
    """'Scarlet & Violet Surging Sparks (2024)' → 'Surging Sparks'"""
    name = re.sub(r'\s*\(\d{4}\)\s*$', '', full).strip()
    for prefix in _ERA_PREFIXES:
        if name.startswith(prefix):
            return name[len(prefix):]
    return name

# ── All sets from Base Set (1999) through 2026 ───────────────────────────────
ALL_SETS = [
    # ── Wizards of the Coast era (1999–2003) ──
    ("base1",    "Base Set (1999)"),
    ("base2",    "Jungle (1999)"),
    ("base3",    "Fossil (1999)"),
    ("base4",    "Base Set 2 (2000)"),
    ("base5",    "Team Rocket (2000)"),
    ("gym1",     "Gym Heroes (2000)"),
    ("gym2",     "Gym Challenge (2000)"),
    ("neo1",     "Neo Genesis (2000)"),
    ("neo2",     "Neo Discovery (2001)"),
    ("si1",      "Southern Islands (2001)"),
    ("neo3",     "Neo Revelation (2001)"),
    ("neo4",     "Neo Destiny (2002)"),
    ("base6",    "Legendary Collection (2002)"),
    ("ecard1",   "Expedition Base Set (2002)"),
    ("ecard2",   "Aquapolis (2003)"),
    ("ecard3",   "Skyridge (2003)"),
    # ── EX / Ruby & Sapphire era (2003–2007) ──
    ("ex1",      "EX Ruby & Sapphire (2003)"),
    ("ex2",      "EX Sandstorm (2003)"),
    ("ex3",      "EX Dragon (2003)"),
    ("ex4",      "EX Team Magma vs Team Aqua (2004)"),
    ("ex5",      "EX Hidden Legends (2004)"),
    ("ex6",      "EX FireRed & LeafGreen (2004)"),
    ("ex7",      "EX Team Rocket Returns (2004)"),
    ("ex8",      "EX Deoxys (2005)"),
    ("ex9",      "EX Emerald (2005)"),
    ("ex10",     "EX Unseen Forces (2005)"),
    ("ex11",     "EX Delta Species (2005)"),
    ("ex12",     "EX Legend Maker (2006)"),
    ("ex13",     "EX Holon Phantoms (2006)"),
    ("ex14",     "EX Crystal Guardians (2006)"),
    ("ex15",     "EX Dragon Frontiers (2006)"),
    ("ex16",     "EX Power Keepers (2007)"),
    # ── Diamond & Pearl era (2007–2009) ──
    ("dp1",      "Diamond & Pearl Base Set (2007)"),
    ("dp2",      "Diamond & Pearl Mysterious Treasures (2007)"),
    ("dp3",      "Diamond & Pearl Secret Wonders (2007)"),
    ("dp4",      "Diamond & Pearl Great Encounters (2008)"),
    ("dp5",      "Diamond & Pearl Majestic Dawn (2008)"),
    ("dp6",      "Diamond & Pearl Legends Awakened (2008)"),
    ("dp7",      "Diamond & Pearl Stormfront (2008)"),
    ("pl1",      "Platinum Base Set (2009)"),
    ("pl2",      "Platinum Rising Rivals (2009)"),
    ("pl3",      "Platinum Supreme Victors (2009)"),
    ("pl4",      "Platinum Arceus (2009)"),
    # ── HeartGold & SoulSilver era (2010–2011) ──
    ("hgss1",    "HeartGold & SoulSilver Base Set (2010)"),
    ("hgss2",    "HS Unleashed (2010)"),
    ("hgss3",    "HS Undaunted (2010)"),
    ("hgss4",    "HS Triumphant (2010)"),
    ("col1",     "Call of Legends (2011)"),
    # ── Black & White era (2011–2013) ──
    ("bw1",      "Black & White Base Set (2011)"),
    ("bw2",      "Black & White Emerging Powers (2011)"),
    ("bw3",      "Black & White Noble Victories (2011)"),
    ("bw4",      "Black & White Next Destinies (2012)"),
    ("bw5",      "Black & White Dark Explorers (2012)"),
    ("bw6",      "Black & White Dragons Exalted (2012)"),
    ("dv1",      "Dragon Vault (2012)"),
    ("bw7",      "Black & White Boundaries Crossed (2012)"),
    ("bw8",      "Black & White Plasma Storm (2013)"),
    ("bw9",      "Black & White Plasma Freeze (2013)"),
    ("bw10",     "Black & White Plasma Blast (2013)"),
    ("bw11",     "Black & White Legendary Treasures (2013)"),
    # XY Era
    ("xy1",      "XY Base Set (2014)"),
    ("xy2",      "XY Flashfire (2014)"),
    ("xy3",      "XY Furious Fists (2014)"),
    ("xy4",      "XY Phantom Forces (2014)"),
    ("xy5",      "XY Primal Clash (2015)"),
    ("xy6",      "XY Roaring Skies (2015)"),
    ("xy7",      "XY Ancient Origins (2015)"),
    ("xy8",      "XY BREAKthrough (2015)"),
    ("xy9",      "XY BREAKpoint (2016)"),
    ("xy10",     "XY Fates Collide (2016)"),
    ("xy11",     "XY Steam Siege (2016)"),
    ("xy12",     "XY Evolutions (2016)"),
    ("dc1",      "Double Crisis (2015)"),
    ("g1",       "Generations (2016)"),
    # Sun & Moon Era
    ("sm1",      "Sun & Moon Base Set (2017)"),
    ("sm2",      "Sun & Moon Guardians Rising (2017)"),
    ("sm3",      "Sun & Moon Burning Shadows (2017)"),
    ("sm4",      "Sun & Moon Crimson Invasion (2017)"),
    ("sm5",      "Sun & Moon Ultra Prism (2018)"),
    ("sm6",      "Sun & Moon Forbidden Light (2018)"),
    ("sm7",      "Sun & Moon Celestial Storm (2018)"),
    ("sm75",     "Sun & Moon Dragon Majesty (2018)"),
    ("sm8",      "Sun & Moon Lost Thunder (2018)"),
    ("sm9",      "Sun & Moon Team Up (2019)"),
    ("sm10",     "Sun & Moon Unbroken Bonds (2019)"),
    ("sm11",     "Sun & Moon Unified Minds (2019)"),
    ("sm35",     "Sun & Moon Shining Legends (2017)"),
    ("sm115",    "Sun & Moon Hidden Fates (2019)"),
    ("det1",     "Detective Pikachu (2019)"),
    ("sm12",     "Sun & Moon Cosmic Eclipse (2019)"),
    # Sword & Shield Era
    ("swsh1",    "Sword & Shield Base Set (2020)"),
    ("swsh2",    "Sword & Shield Rebel Clash (2020)"),
    ("swsh3",    "Sword & Shield Darkness Ablaze (2020)"),
    ("swsh35",   "Champion's Path (2020)"),
    ("swsh4",    "Sword & Shield Vivid Voltage (2020)"),
    ("swsh45",   "Shining Fates (2021)"),
    ("swsh5",    "Sword & Shield Battle Styles (2021)"),
    ("swsh6",    "Sword & Shield Chilling Reign (2021)"),
    ("swsh7",    "Sword & Shield Evolving Skies (2021)"),
    ("cel25",    "Celebrations (2021)"),
    ("swsh8",    "Sword & Shield Fusion Strike (2021)"),
    ("swsh9",    "Sword & Shield Brilliant Stars (2022)"),
    ("swsh10",   "Sword & Shield Astral Radiance (2022)"),
    ("pgo",      "Pokémon GO (2022)"),
    ("swsh11",   "Sword & Shield Lost Origin (2022)"),
    ("swsh12",   "Silver Tempest (2022)"),
    ("swsh12pt5","Crown Zenith (2023)"),
    # Scarlet & Violet Era
    ("sv1",      "Scarlet & Violet Base Set (2023)"),
    ("sv2",      "Scarlet & Violet Paldea Evolved (2023)"),
    ("sv3",      "Scarlet & Violet Obsidian Flames (2023)"),
    ("sv3pt5",   "Scarlet & Violet 151 (2023)"),
    ("sv4",      "Scarlet & Violet Paradox Rift (2023)"),
    ("sv4pt5",   "Scarlet & Violet Paldean Fates (2024)"),
    ("sv5",      "Scarlet & Violet Temporal Forces (2024)"),
    ("sv6",      "Scarlet & Violet Twilight Masquerade (2024)"),
    ("sv6pt5",   "Scarlet & Violet Shrouded Fable (2024)"),
    ("sv7",      "Scarlet & Violet Stellar Crown (2024)"),
    ("sv8",      "Scarlet & Violet Surging Sparks (2024)"),
    ("sv8pt5",   "Prismatic Evolutions (2025)"),
    ("sv9",      "Scarlet & Violet Journey Together (2025)"),
    ("sv10",     "Scarlet & Violet Destined Rivals (2025)"),
    ("rsv10pt5", "White Flare (2025)"),
    ("zsv10pt5", "Black Bolt (2025)"),
    ("me1",      "Mega Evolution (2025)"),
    ("me2",      "Phantasmal Flames (2025)"),
    ("me2pt5",   "Ascended Heroes (2026)"),
    ("me3",      "Perfect Order (2026)"),
    ("me4",      "Chaos Rising (2026)"),
    # Promo sets
    ("svp",      "Scarlet & Violet Promos"),
    ("swshp",    "Sword & Shield Promos"),
    ("smp",      "Sun & Moon Promos"),
    ("xyp",      "XY Promos"),
    ("bwp",      "Black & White Promos"),
    ("hsp",      "HeartGold & SoulSilver Promos"),
    ("dpp",      "Diamond & Pearl Promos"),
    ("np",       "Nintendo Black Star Promos"),
    ("basep",    "Wizards Black Star Promos"),
    ("bp",       "Best of Game"),
    # POP Series
    ("pop1",     "POP Series 1 (2004)"),
    ("pop2",     "POP Series 2 (2005)"),
    ("pop3",     "POP Series 3 (2006)"),
    ("pop4",     "POP Series 4 (2006)"),
    ("pop5",     "POP Series 5 (2007)"),
    ("pop6",     "POP Series 6 (2007)"),
    ("pop7",     "POP Series 7 (2008)"),
    ("pop8",     "POP Series 8 (2008)"),
    ("pop9",     "POP Series 9 (2009)"),
    # McDonald's Collections
    ("mcd11",    "McDonald's Collection 2011"),
    ("mcd12",    "McDonald's Collection 2012"),
    ("mcd14",    "McDonald's Collection 2014"),
    ("mcd15",    "McDonald's Collection 2015"),
    ("mcd16",    "McDonald's Collection 2016"),
    ("mcd17",    "McDonald's Collection 2017"),
    ("mcd18",    "McDonald's Collection 2018"),
    ("mcd19",    "McDonald's Collection 2019"),
    ("mcd21",    "McDonald's Collection 2021"),
    ("mcd22",    "McDonald's Collection 2022"),
    # Misc special sets
    ("ru1",      "Pokémon Rumble (2009)"),
    ("fut20",    "Pokémon Futsal Collection (2020)"),
]

SET_CHOICES = [('', '— select set —')] + [(code, shorten_set_name(label)) for code, label in ALL_SETS]


# ── All Japanese sets from XY (2013) through 2025 ────────────────────────────
# Codes match the official Japanese expansion codes used on pokemon-card.com
# and in community databases (Bulbapedia, Serebii, etc.)
ALL_SETS_KO = [
    # Sun & Moon Era (Korea released 2017–2019)
    ("SM1S",  "Collection Sun (2017)"),
    ("SM1M",  "Collection Moon (2017)"),
    ("SM2K",  "Islands Await You (2017)"),
    ("SM2L",  "Alolan Moonlight (2017)"),
    ("SM3H",  "Shining Legends (2017)"),
    ("SM3N",  "Light-Devouring Darkness (2017)"),
    ("SM4S",  "Awakened Heroes (2017)"),
    ("SM4A",  "Ultradimensional Beasts (2017)"),
    ("SM5S",  "Ultra Sun (2018)"),
    ("SM5M",  "Ultra Moon (2018)"),
    ("SM6",   "Forbidden Light (2018)"),
    ("SM6a",  "Dragon Storm (2018)"),
    ("SM6b",  "Champion Road (2018)"),
    ("SM7",   "Celestial Storm (2018)"),
    ("SM7a",  "Plasma Spark (2018)"),
    ("SM7b",  "Fairy Rise (2018)"),
    ("SM8",   "Burst Impact (2018)"),
    ("SM8a",  "Dark Order (2018)"),
    ("SM8b",  "GX Ultra Shiny Ultimate (2018)"),
    ("SM9",   "Tag Bolt (2018)"),
    ("SM9a",  "Night Unison (2019)"),
    ("SM9b",  "Full Metal Wall (2019)"),
    ("SM10",  "Double Blaze (2019)"),
    ("sn10a", "GG End (2019)"),
    ("SM10b", "Sky Legend (2019)"),
    ("sn11",  "Miracle Twin (2019)"),
    ("SM11a", "Remix Bout (2019)"),
    ("SM11b", "Dream League (2019)"),
    ("SM12",  "Alter Genesis (2019)"),
    ("SM12a", "TAG TEAM GX Tag All Stars (2019)"),
    # Sword & Shield Era (Korea released 2020–2022)
    ("S1W",   "Sword (2020)"),
    ("S1H",   "Shield (2020)"),
    ("S1a",   "VMAX Rising (2020)"),
    ("S2",    "Rebellion Crash (2020)"),
    ("S2a",   "Explosive Walker (2020)"),
    ("S3",    "Infinite Zone (2020)"),
    ("S3a",   "Legendary Heartbeat (2020)"),
    ("S4",    "Amazing Volt Tackle (2020)"),
    ("S4a",   "Shiny Star V (2020)"),
    ("S5I",   "Single Strike Master (2021)"),
    ("S5R",   "Rapid Strike Master (2021)"),
    ("S5a",   "Twin Champions (2021)"),
    ("S6H",   "Silver Lance (2021)"),
    ("S6K",   "Jet-Black Geist (2021)"),
    ("S6a",   "Eevee Heroes (2021)"),
    ("S7D",   "Skyscraping Perfection (2021)"),
    ("S7R",   "Blue Sky Stream (2021)"),
    ("S8",    "Fusion Arts (2021)"),
    ("S8a",   "25th Anniversary (2021)"),
    ("S8b",   "VMAX Climax (2021)"),
    ("S9",    "Star Birth (2022)"),
    ("S9a",   "Battle Region (2022)"),
    ("S10D",  "Time Gazer (2022)"),
    ("S10P",  "Space Juggler (2022)"),
    ("S10a",  "Dark Phantasma (2022)"),
    ("S10b",  "Pokémon GO (2022)"),
    ("S11",   "Lost Abyss (2022)"),
    ("S11a",  "Incandescent Arcana (2022)"),
    ("S12",   "Paradigm Trigger (2022)"),
    ("S12a",  "VSTAR Universe (2022)"),
    # Scarlet & Violet Era (Korea released 2023–present)
    ("SV1S",  "Scarlet ex (2023)"),
    ("SV1V",  "Violet ex (2023)"),
    ("SV1a",  "Triple Beat (2023)"),
    ("SV2D",  "Clay Burst (2023)"),
    ("SV2P",  "Snow Hazard (2023)"),
    ("SV2a",  "Pokémon Card 151 (2023)"),
    ("SV3",   "Ruler of the Black Flame (2023)"),
    ("SV3a",  "Raging Surf (2023)"),
    ("SV4K",  "Ancient Roar (2023)"),
    ("SV4M",  "Future Flash (2023)"),
    ("SV4a",  "Shiny Treasure ex (2023)"),
    ("SV5K",  "Wild Force (2024)"),
    ("SV5M",  "Cyber Judge (2024)"),
    ("SV5a",  "Crimson Haze (2024)"),
    ("SV6",   "Mask of Change (2024)"),
]

ALL_SETS_JA = [
    # Classic Era — Base Set (1996)
    ("PMCG1", "Base Set (1996)"),
    ("PMCG2", "Jungle (1997)"),
    ("PMCG3", "Fossil (1997)"),
    ("PMCG4", "Rocket Gang (1997)"),
    ("PMCG5", "Leaders' Stadium (1997)"),
    ("PMCG6", "Challenge from the Darkness (1998)"),
    # Neo Era (1999–2001)
    ("neo1",  "Gold, Silver, to a New World (1999)"),
    ("neo2",  "Crossing the Ruins (2000)"),
    ("neo3",  "Awakening Legends (2000)"),
    ("neo4",  "Darkness, and to Light (2001)"),
    # VS / web (2001–2002)
    ("VS1",   "Pokémon Card VS (2001)"),
    ("web1",  "Pokémon Card web (2002)"),
    # e-Card Era (2001–2002)
    ("E1",    "Base Expansion Pack (2001)"),
    ("E2",    "Town on No Map (2001)"),
    ("E3",    "Wind from the Sea (2002)"),
    ("E4",    "Split Earth (2002)"),
    ("E5",    "Mysterious Mountains (2002)"),
    # PCG Era — FireRed/LeafGreen (2004–2007)
    ("PCG1",  "Legend of the Skies (2004)"),
    ("PCG2",  "Clash of the Blue Sky (2004)"),
    ("PCG3",  "Rocket Gang Strikes Back (2004)"),
    ("PCG4",  "Golden Sky, Silvery Ocean (2005)"),
    ("PCG5",  "Mirage Forest (2005)"),
    ("PCG6",  "Holon Research Tower (2006)"),
    ("PCG7",  "Holon Phantom (2006)"),
    ("PCG8",  "Crystal Guardians (2006)"),
    ("PCG9",  "Shores of Conflict (2007)"),
    # Mega Series (2014–2016 Japanese-only)
    ("M1L",   "Mega Brave (2014)"),
    ("M1S",   "Mega Sinfonia (2014)"),
    ("M2",    "Inferno X (2015)"),
    ("M3",    "Muniqueeze Zero (2016)"),
    # XY Era  (Japan released Nov 2013 – Dec 2016)
    ("XY1a",   "Collection X (2013)"),
    ("XY1b",   "Collection Y (2013)"),
    ("XY2",    "Wild Blaze (2014)"),
    ("XY3",    "Rising Fist (2014)"),
    ("XY4",    "Phantom Gate (2014)"),
    ("XY5a",   "Gaia Volcano (2015)"),
    ("XY5b",   "Tidal Storm (2015)"),
    ("XY6",    "Emerald Break (2015)"),
    ("XY7",    "Bandit Ring (2015)"),
    ("XY8a",   "Blue Shock (2015)"),
    ("XY8b",   "Red Flash (2015)"),
    ("XY9",    "Rage of the Broken Heavens (2016)"),
    ("XY10",   "Awakening Psychic King (2016)"),
    ("XY11a",  "Blue Impact (2016)"),
    ("XY11b",  "Red Excitement (2016)"),
    ("XY-P",   "XY Promos"),
    # Sun & Moon Era  (Japan released Dec 2016 – Oct 2019)
    ("SM1S",   "Collection Sun (2016)"),
    ("SM1M",   "Collection Moon (2016)"),
    ("SM2K",   "Islands Await You (2017)"),
    ("SM2L",   "Alolan Moonlight (2017)"),
    ("SM3H",   "Shining Legends (2017)"),
    ("SM4S",   "Awakened Heroes (2017)"),
    ("SM4A",   "Ultradimensional Beasts (2017)"),
    ("SM5S",   "Ultra Sun (2018)"),
    ("SM5M",   "Ultra Moon (2018)"),
    ("SM6",    "Forbidden Light (2018)"),
    ("SM6a",   "Dragon Storm (2018)"),
    ("SM6b",   "Champion Road (2018)"),
    ("SM7",    "Celestial Storm (2018)"),
    ("SM7a",   "Thunderclap Spark (2018)"),
    ("SM7b",   "Fairy Rise (2018)"),
    ("SM8",    "Lost Thunder (2018)"),
    ("SM8a",   "Dark Order (2018)"),
    ("SM8b",   "GX Ultra Shiny (2018)"),
    ("SM9",    "Tag Bolt (2018)"),
    ("SM9a",   "Night Unison (2019)"),
    ("SM9b",   "Full Metal Wall (2019)"),
    ("SM10",   "Double Blaze (2019)"),
    ("SM10b",  "Sky Legend (2019)"),
    ("SM11a",  "Remix Bout (2019)"),
    ("SM11b",  "Dream League (2019)"),
    ("SM12",   "Alter Genesis (2019)"),
    ("SM12a",  "Tag All Stars (2019)"),
    ("SM-P",   "Sun & Moon Promos"),
    # Sword & Shield Era  (Japan released Jan 2020 – Dec 2022)
    ("S1W",    "Sword (2020)"),
    ("S1H",    "Shield (2020)"),
    ("S2",     "Rebellion Crash (2020)"),
    ("S2a",    "Explosive Walker (2020)"),
    ("S3",     "Infinity Zone (2020)"),
    ("S3a",    "Legendary Heartbeat (2020)"),
    ("S4",     "Amazing Volt Tackle (2020)"),
    ("S4a",    "Shiny Star V (2020)"),
    ("S5I",    "Single Strike Master (2021)"),
    ("S5R",    "Rapid Strike Master (2021)"),
    ("S6H",    "Silver Lance (2021)"),
    ("S6K",    "Jet-Black Spirit (2021)"),
    ("S6a",    "Eevee Heroes (2021)"),
    ("S7D",    "Skyscraping Perfection (2021)"),
    ("S7R",    "Blue Sky Stream (2021)"),
    ("S8",     "Fusion Arts (2021)"),
    ("S8a",    "25th Anniversary Collection (2021)"),
    ("S8b",    "VMAX Climax (2021)"),
    ("S9",     "Star Birth (2022)"),
    ("S9a",    "Battle Region (2022)"),
    ("S10D",   "Time Gazer (2022)"),
    ("S10P",   "Space Juggler (2022)"),
    ("S10a",   "Dark Phantasma (2022)"),
    ("S10b",   "Pokémon GO (2022)"),
    ("S11",    "Lost Abyss (2022)"),
    ("S11a",   "Incandescent Arcana (2022)"),
    ("S12",    "Paradigm Trigger (2022)"),
    ("S12a",   "VSTAR Universe (2022)"),
    ("SW-P",   "Sword & Shield Promos"),
    # Scarlet & Violet Era  (Japan released Jan 2023 – present)
    ("SV1S",   "Scarlet ex (2023)"),
    ("SV1V",   "Violet ex (2023)"),
    ("SV1a",   "Triple Beat (2023)"),
    ("SV2D",   "Snow Hazard (2023)"),
    ("SV2P",   "Clay Burst (2023)"),
    ("SV2a",   "Pokémon Card 151 (2023)"),
    ("SV3",    "Ruler of the Black Flame (2023)"),
    ("SV3a",   "Raging Surf (2023)"),
    ("SV4K",   "Ancient Roar (2023)"),
    ("SV4M",   "Future Flash (2023)"),
    ("SV4a",   "Shiny Treasure ex (2023)"),
    ("SV5K",   "Wild Force (2024)"),
    ("SV5M",   "Cyber Judge (2024)"),
    ("SV5a",   "Crimson Haze (2024)"),
    ("SV6",    "Mask of Change (2024)"),
    ("SV6a",   "Night Wanderer (2024)"),
    ("SV7",    "Stellar Miracle (2024)"),
    ("SV7a",   "Paradise Dragona (2024)"),
    ("SV8",    "Super Electric Breaker (2024)"),
    ("SV8a",   "Terastal Festival ex (2024)"),
    ("SV9",    "Battle Partners (2025)"),
    ("SV9a",   "Tera Champions (2025)"),
    ("SV10",   "Destined Rivals (2025)"),
    ("SV11B",  "Black Bolt (2025)"),
    ("SV11W",  "White Flare (2025)"),
    # SV special / starter sets
    ("SVLN",   "Starter Set Stellar Ninfia ex (2024)"),
    ("SVLS",   "Starter Set Stellar Soublaze ex (2024)"),
    ("SVK",    "Deck Build Box Stellar Miracle (2024)"),
    ("SV-P",   "Scarlet & Violet Promos"),
]


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Create Account')


class CardForm(FlaskForm):
    name = StringField('Pokémon Name', validators=[DataRequired(), Length(max=100)])
    card_number = StringField('Card Number (e.g. 4/102)', validators=[Optional(), Length(max=20)])
    set_code = SelectField('Set', choices=SET_CHOICES, validators=[Optional()])
    rarity = SelectField('Rarity', choices=[
        ('', '— select —'),
        ('Common', 'Common'),
        ('Uncommon', 'Uncommon'),
        ('Rare', 'Rare'),
        ('Holo Rare', 'Holo Rare'),
        ('Reverse Holo', 'Reverse Holo'),
        ('Ultra Rare', 'Ultra Rare'),
        ('Secret Rare', 'Secret Rare'),
        ('Full Art', 'Full Art'),
        ('Rainbow Rare', 'Rainbow Rare'),
        ('Gold Rare', 'Gold Rare'),
        ('Promo', 'Promo'),
        ('Special Illustration Rare', 'Special Illustration Rare'),
        ('Hyper Rare', 'Hyper Rare'),
        ('Double Rare', 'Double Rare'),
        ('Illustration Rare', 'Illustration Rare'),
    ], validators=[Optional()])
    card_type = SelectField('Card Type', choices=[
        ('Pokemon', 'Pokémon'),
        ('Trainer', 'Trainer'),
        ('Energy', 'Energy'),
    ], default='Pokemon')
    pokemon_type = SelectField('Pokémon Type', choices=[
        ('', '— select —'),
        ('Colorless', 'Colorless'), ('Fire', 'Fire'), ('Water', 'Water'),
        ('Grass', 'Grass'), ('Lightning', 'Lightning'), ('Psychic', 'Psychic'),
        ('Fighting', 'Fighting'), ('Darkness', 'Darkness'), ('Metal', 'Metal'),
        ('Fairy', 'Fairy'), ('Dragon', 'Dragon'),
    ], validators=[Optional()])
    hp = IntegerField('HP', validators=[Optional(), NumberRange(min=0, max=999)])
    quantity = IntegerField('Quantity', default=1, validators=[NumberRange(min=1)])
    is_foil   = BooleanField('Foil / Holo')
    is_graded = BooleanField('Graded')
    grade     = StringField('Grade (e.g. PSA 10)', validators=[Optional(), Length(max=10)])
    purchase_price = FloatField('Purchase Price ($)', validators=[Optional()])
    image_url  = StringField('Card Image URL', validators=[Optional(), Length(max=500)])
    card_image = FileField('Upload Card Image', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'webp'], 'Images only!')
    ])
    notes = TextAreaField('Notes', validators=[Optional(), Length(max=1000)])
    submit = SubmitField('Save Card')


VARIANT_CHOICES = [
    ('Standard',                  'Standard'),
    ('Holo',                      'Holo'),
    ('Reverse Holo',              'Reverse Holo'),
    ('Full Art',                  'Full Art'),
    ('EX',                        'EX'),
    ('GX',                        'GX'),
    ('V',                         'V'),
    ('VStar',                     'VStar'),
    ('VMax',                      'VMax'),
    ('BREAK',                     'BREAK'),
    ('Prism Star',                'Prism Star'),
    ('Amazing Rare',              'Amazing Rare'),
    ('Illustration Rare',         'Illustration Rare'),
    ('Special Illustration Rare', 'Special Illustration Rare'),
    ('Rainbow Rare',              'Rainbow Rare'),
    ('Gold',                      'Gold'),
    ('Secret Rare',               'Secret Rare'),
    ('Special',                   'Special'),
]


class EditCardForm(FlaskForm):
    purchase_price = FloatField('Purchase Price', validators=[Optional()])
    notes          = TextAreaField('Notes', validators=[Optional(), Length(max=1000)])
    submit         = SubmitField('Save Changes')


class SearchForm(FlaskForm):
    q = StringField('Search', validators=[Optional()])
    submit = SubmitField('Search')
