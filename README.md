# PokéVault 🃏

A Pokemon card collection tracker built with Flask. Track your cards, monitor value, and search your collection.

## Features

- **Dashboard** — overview of your collection with total value, gain/loss, rarity/set breakdowns, top cards
- **Collection browser** — sort by name, value, set, recency; filter by type and rarity
- **Search** — search cards by Pokémon name, card number (e.g. `4/102`), set name, or set code
- **Card detail** — condition, grade, purchase price, market price, profit/loss, notes
- **Add/Edit/Delete** cards with image URL or file upload
- **User accounts** — register, login, logout with Flask-Login + hashed passwords
- **Admin dashboard** — user management (set `role = 'admin'` in the DB)
- **Price API ready** — stub at `/api/cards/refresh-prices` wired to Pokemon TCG API

## Setup

### 1. Clone and enter project

```bash
cd pokemon_cards
```

### 2. Virtual environment

```bash
python -m venv venv
source venv/bin/activate       # macOS / Linux
venv\Scripts\activate          # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure `.flaskenv`

```
FLASK_APP=main.py
FLASK_DEBUG=1
SQLITE_DB=pokemon.db
FLASK_RUN_HOST=0.0.0.0
FLASK_RUN_PORT=8080
SECRET_KEY=your-secret-key-here
```

### 5. Initialize the database

```bash
flask db init
flask db migrate -m "initial"
flask db upgrade
```

### 6. Run

```bash
flask run
```

Open `http://127.0.0.1:8080`

## Adding Pokemon TCG API (price data)

1. Get a free API key at https://dev.pokemontcg.io/
2. Add `POKEMON_TCG_API_KEY=your-key` to `.flaskenv`
3. Implement `refresh_prices()` in `app/routes.py` — the stub is already there

## Project Structure

```
pokemon_cards/
├── app/
│   ├── __init__.py      # Flask app factory, db, login manager
│   ├── models.py        # User + Card SQLAlchemy models
│   ├── routes.py        # All Flask routes
│   ├── forms.py         # WTForms
│   ├── static/
│   │   ├── style.css
│   │   ├── placeholder.png
│   │   └── uploads/     # User-uploaded card images
│   └── templates/
│       ├── base.html
│       ├── dashboard.html
│       ├── collection.html
│       ├── search.html
│       ├── view_card.html
│       ├── card_form.html
│       ├── login.html
│       ├── register.html
│       ├── admin.html
│       └── errors/
├── migrations/
├── main.py
├── requirements.txt
└── .flaskenv
```

## Key Routes

| Route | Description |
|---|---|
| `/` | Dashboard — collection overview |
| `/collection` | All your cards with sort/filter |
| `/search?q=charizard` | Search results |
| `/card/add` | Add a new card |
| `/card/<id>` | Card detail view |
| `/card/<id>/edit` | Edit a card |
| `/admin` | Admin dashboard (admin role only) |
