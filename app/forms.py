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

# ── All sets from XY (2014) through 2026 ─────────────────────────────────────
ALL_SETS = [
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
    ("sm115",    "Sun & Moon Hidden Fates (2019)"),
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
]

SET_CHOICES = [('', '— select set —')] + [(code, shorten_set_name(label)) for code, label in ALL_SETS]


# ── All Japanese sets from XY (2013) through 2025 ────────────────────────────
# Codes match the official Japanese expansion codes used on pokemon-card.com
# and in community databases (Bulbapedia, Serebii, etc.)
ALL_SETS_JA = [
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
