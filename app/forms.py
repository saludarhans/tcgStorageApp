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
    ("sv10pt5",  "Mega Evolution (2025)"),
    ("sv11wf",   "White Flare (2025)"),
    ("sv11bb",   "Black Bolt (2025)"),
    ("sv12",     "Phantasmal Flames (2025)"),
    ("sv13",     "Ascended Heroes (2026)"),
    ("sv14",     "Perfect Order (2026)"),
]

SET_CHOICES = [('', '— select set —')] + [(code, shorten_set_name(label)) for code, label in ALL_SETS]


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
    condition = SelectField('Condition', choices=[
        ('M',   'Mint (M)'),
        ('NM',  'Near Mint (NM)'),
        ('LP',  'Lightly Played (LP)'),
        ('MP',  'Moderately Played (MP)'),
        ('HP',  'Heavily Played (HP)'),
        ('DMG', 'Damaged (DMG)'),
    ], default='NM')
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


class SearchForm(FlaskForm):
    q = StringField('Search', validators=[Optional()])
    submit = SubmitField('Search')
