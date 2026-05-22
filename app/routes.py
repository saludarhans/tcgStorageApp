import os
import uuid
from datetime import datetime
from flask import render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import text
from werkzeug.utils import secure_filename

from app import app, db
from app.models import User, Card, CardCatalog
from app.forms import LoginForm, RegisterForm, CardForm, EditCardForm, SearchForm, ALL_SETS, shorten_set_name

SET_CODE_TO_NAME = {code: shorten_set_name(name) for code, name in ALL_SETS}

# Chronological set ordering: CASE WHEN set_code='xy1' THEN 0 WHEN ... END
_when = ' '.join(f"WHEN set_code='{code}' THEN {i}" for i, (code, _) in enumerate(ALL_SETS))
_SET_AGE_EXPR = text(f"CASE {_when} ELSE {len(ALL_SETS)} END")

# Numeric card-number ordering: treats '10' as 10 not '10', non-numeric sorts last
_NUM_EXPR = text("CASE WHEN card_number GLOB '[0-9]*' THEN CAST(card_number AS INTEGER) ELSE 9999 END")


def detect_variant(name, rarity, is_foil=False):
    """Infer card variant from name, rarity string, and foil flag."""
    r = (rarity or '').lower()
    n = (name or '').lower()
    if 'special illustration rare' in r: return 'Special Illustration Rare'
    if 'illustration rare'         in r: return 'Illustration Rare'
    if 'hyper rare'                in r: return 'Gold'
    if 'rare rainbow' in r or 'rainbow rare' in r: return 'Rainbow Rare'
    if 'rare secret'  in r or 'secret rare'  in r: return 'Secret Rare'
    if 'rare ultra'   in r:              return 'Full Art'
    if 'amazing rare' in r:              return 'Amazing Rare'
    if 'prism star'   in r:              return 'Prism Star'
    if 'rare break'   in r or n.endswith(' break'): return 'BREAK'
    if 'vmax' in n: return 'VMax'
    if 'vstar' in n: return 'VStar'
    if n.endswith('-gx') or n.endswith(' gx') or 'rare holo gx' in r or 'shiny gx' in r:
        return 'GX'
    if n.endswith('-ex') or n.endswith(' ex') or 'holo ex' in r:
        return 'EX'
    if ('rare holo v' in r and 'vmax' not in r and 'vstar' not in r) or \
       (n.endswith(' v') and 'vmax' not in n and 'vstar' not in n):
        return 'V'
    if 'reverse holo' in r:          return 'Reverse Holo'
    if 'holo' in r or bool(is_foil): return 'Holo'
    return 'Special'


# ─── Auth ────────────────────────────────────────────────────────────────────

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(next_page or url_for('dashboard'))
        flash('Invalid username or password.', 'danger')
    return render_template('login.html', form=form, title='Sign In')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already taken.', 'danger')
            return render_template('register.html', form=form, title='Register')
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already registered.', 'danger')
            return render_template('register.html', form=form, title='Register')
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Account created! Please sign in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form, title='Register')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been signed out.', 'info')
    return redirect(url_for('login'))


# ─── Dashboard / Landing ─────────────────────────────────────────────────────

@app.route('/')
@login_required
def dashboard():
    cards = current_user.cards.order_by(Card.added_at.desc()).all()

    total_cards = len(cards)
    unique_pokemon = len(set(c.name.lower() for c in cards))
    total_value = sum((c.market_price or 0) * c.quantity for c in cards)
    total_cost = sum((c.purchase_price or 0) * c.quantity for c in cards)
    cards_with_cost = [c for c in cards if c.purchase_price]
    profit_loss = (total_value - total_cost) if cards_with_cost else None

    # Top 5 most valuable
    top_cards = sorted([c for c in cards if c.market_price], key=lambda c: c.market_price, reverse=True)[:5]

    # Recent additions
    recent_cards = cards[:6]

    # By rarity breakdown
    rarity_counts = {}
    for c in cards:
        r = c.rarity or 'Unknown'
        rarity_counts[r] = rarity_counts.get(r, 0) + 1

    # By set breakdown
    set_counts = {}
    for c in cards:
        s = c.set_name or 'Unknown'
        set_counts[s] = set_counts.get(s, 0) + 1

    return render_template('dashboard.html',
                           title='My Collection',
                           cards=cards,
                           total_cards=total_cards,
                           unique_pokemon=unique_pokemon,
                           total_value=total_value,
                           total_cost=total_cost,
                           profit_loss=profit_loss,
                           top_cards=top_cards,
                           recent_cards=recent_cards,
                           rarity_counts=rarity_counts,
                           set_counts=set_counts)


# ─── Collection (all cards) ──────────────────────────────────────────────────

@app.route('/collection')
@login_required
def collection():
    sort = request.args.get('sort', 'recent')
    filter_type = request.args.get('type', '')
    filter_rarity = request.args.get('rarity', '')

    query = current_user.cards

    if filter_type:
        query = query.filter(Card.card_type == filter_type)
    if filter_rarity:
        query = query.filter(Card.rarity == filter_rarity)

    if sort == 'name':
        query = query.order_by(Card.name)
    elif sort == 'value':
        query = query.order_by(Card.market_price.desc().nullslast())
    elif sort == 'set':
        query = query.order_by(Card.set_name, Card.card_number)
    else:
        query = query.order_by(Card.added_at.desc())

    cards = query.all()

    rarities = db.session.query(Card.rarity).filter(
        Card.user_id == current_user.id, Card.rarity != None
    ).distinct().all()
    rarities = [r[0] for r in rarities]

    return render_template('collection.html',
                           title='My Collection',
                           cards=cards,
                           rarities=rarities,
                           current_sort=sort,
                           current_type=filter_type,
                           current_rarity=filter_rarity)


# ─── Search ──────────────────────────────────────────────────────────────────

@app.route('/search')
@login_required
def search():
    q = request.args.get('q', '').strip()
    results = []
    owned_keys = set()

    if len(q) >= 2:
        results = (CardCatalog.query
                   .filter(CardCatalog.name.ilike(f'{q}%'))
                   .order_by(_SET_AGE_EXPR, _NUM_EXPR, CardCatalog.card_number)
                   .limit(200)
                   .all())
        if results:
            owned_rows = (db.session.query(Card.name, Card.set_code)
                          .filter(Card.user_id == current_user.id,
                                  Card.name.ilike(f'{q}%'))
                          .all())
            owned_keys = {(r.name.lower(), r.set_code) for r in owned_rows}

    return render_template('search.html', title='Search',
                           results=results, owned_keys=owned_keys, query=q)


# ─── Card CRUD ───────────────────────────────────────────────────────────────

@app.route('/card/add')
@login_required
def add_card():
    short_sets = [(code, shorten_set_name(label)) for code, label in ALL_SETS]
    return render_template('add_card.html', title='Add Card', all_sets=short_sets)


@app.route('/card/<int:card_id>')
@login_required
def view_card(card_id):
    card = Card.query.get_or_404(card_id)
    if card.user_id != current_user.id and not current_user.is_admin():
        abort(403)
    return render_template('view_card.html', title=card.name, card=card)


@app.route('/card/<int:card_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_card(card_id):
    card = Card.query.get_or_404(card_id)
    if card.user_id != current_user.id and not current_user.is_admin():
        abort(403)
    form = EditCardForm(obj=card)
    if form.validate_on_submit():
        card.notes          = form.notes.data
        card.purchase_price = form.purchase_price.data
        card.updated_at     = datetime.utcnow()
        db.session.commit()
        flash(f'"{card.name}" updated.', 'success')
        return redirect(url_for('view_card', card_id=card.id))
    return render_template('card_form.html', title='Edit Card', form=form, card=card, action='edit')


@app.route('/card/<int:card_id>/delete', methods=['POST'])
@login_required
def delete_card(card_id):
    card = Card.query.get_or_404(card_id)
    if card.user_id != current_user.id and not current_user.is_admin():
        abort(403)
    name = card.name
    db.session.delete(card)
    db.session.commit()
    flash(f'"{name}" removed from your collection.', 'info')
    return redirect(url_for('collection'))


def _populate_card(card, form):
    card.name = form.name.data
    card.card_number = form.card_number.data
    card.set_code = form.set_code.data
    card.set_name = SET_CODE_TO_NAME.get(form.set_code.data, form.set_code.data)
    card.rarity = form.rarity.data
    card.card_type = form.card_type.data
    card.pokemon_type = form.pokemon_type.data
    card.hp = form.hp.data
    card.quantity = form.quantity.data
    card.is_foil = form.is_foil.data
    card.is_graded = form.is_graded.data
    card.grade = form.grade.data
    card.purchase_price = form.purchase_price.data
    card.notes = form.notes.data
    card.image_url = form.image_url.data
    card.updated_at = datetime.utcnow()

    # Handle image upload
    if form.card_image.data and hasattr(form.card_image.data, 'filename') and form.card_image.data.filename:
        f = form.card_image.data
        ext = f.filename.rsplit('.', 1)[-1].lower()
        filename = f'{uuid.uuid4().hex}.{ext}'
        f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        card.local_image = filename


# ─── Admin ───────────────────────────────────────────────────────────────────

@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin():
        abort(403)
    users = User.query.order_by(User.created_at.desc()).all()
    total_cards = Card.query.count()
    return render_template('admin.html', title='Admin', users=users, total_cards=total_cards)


# ─── API stubs (ready for Pokemon TCG API) ───────────────────────────────────

@app.route('/api/cards/refresh-prices', methods=['POST'])
@login_required
def refresh_prices():
    """
    Placeholder: wire up Pokemon TCG API here.
    POST /api/cards/refresh-prices  →  updates market_price for all user cards
    """
    # TODO: iterate current_user.cards, call Pokemon TCG API, update market_price
    flash('Price refresh coming soon — add your Pokemon TCG API key to .flaskenv!', 'info')
    return redirect(url_for('dashboard'))


@app.route('/api/catalog-add/<tcg_id>', methods=['POST'])
@login_required
def catalog_add(tcg_id):
    """Quick-add a card from the local catalog with default settings."""
    cat = CardCatalog.query.filter_by(tcg_id=tcg_id).first_or_404()
    card = Card(
        user_id      = current_user.id,
        name         = cat.name,
        card_number  = cat.card_number,
        set_name     = cat.set_name,
        set_code     = cat.set_code,
        rarity       = cat.rarity,
        card_type    = cat.supertype or 'Pokemon',
        pokemon_type = (cat.types or '').split(',')[0],
        hp           = cat.hp,
        image_url    = cat.image_large or cat.image_small,
        quantity     = 1,
        is_foil      = 'holo' in (cat.rarity or '').lower(),
        variant      = detect_variant(cat.name, cat.rarity),
        market_price = cat.market_price,
    )
    if cat.market_price:
        card.last_price_update = datetime.utcnow()
    db.session.add(card)
    db.session.commit()
    return jsonify({'ok': True, 'card_id': card.id})


# ─── Error handlers ──────────────────────────────────────────────────────────

@app.errorhandler(403)
def forbidden(e):
    return render_template('errors/403.html'), 403

@app.errorhandler(404)
def not_found(e):
    return render_template('errors/404.html'), 404


@app.route('/api/local-search')
@login_required
def local_search():
    """Search the locally-indexed card catalog."""
    name     = request.args.get('name',     '').strip()
    set_code = request.args.get('set_code', '').strip()
    number   = request.args.get('number',   '').strip()
    era      = request.args.get('era',      '').strip()
    page     = max(int(request.args.get('page', 1) or 1), 1)
    page_size = min(int(request.args.get('pageSize', 20) or 20), 100)

    catalog_total = CardCatalog.query.count()

    has_filter = bool(name or set_code or number or era)
    if not has_filter:
        return jsonify({'data': [], 'totalCount': 0,
                        'catalogEmpty': catalog_total == 0})

    q = CardCatalog.query

    if name:
        q = q.filter(CardCatalog.name.ilike(f'{name}%'))
    if set_code:
        q = q.filter(CardCatalog.set_code == set_code)
    if number:
        q = q.filter(CardCatalog.card_number.ilike(f'{number}%'))
    if era and not set_code:
        q = q.filter(CardCatalog.era == era)

    total = q.count()
    cards = (q.order_by(_SET_AGE_EXPR, _NUM_EXPR, CardCatalog.card_number)
              .offset((page - 1) * page_size)
              .limit(page_size)
              .all())

    return jsonify({
        'data':         [c.to_api_dict() for c in cards],
        'totalCount':   total,
        'catalogEmpty': catalog_total == 0,
    })


@app.route('/api/tcg-search')
@login_required
def tcg_search():
    """Proxy to Pokemon TCG API — keeps the API key server-side."""
    import requests as req
    q        = request.args.get('q', 'name:*')
    page     = request.args.get('page', 1)
    pageSize = request.args.get('pageSize', 20)

    api_key = os.environ.get('POKEMON_TCG_API_KEY', '')
    headers = {'X-Api-Key': api_key} if api_key else {}

    try:
        r = req.get(
            'https://api.pokemontcg.io/v2/cards',
            params={'q': q, 'page': page, 'pageSize': pageSize,
                    'select': 'id,name,number,rarity,supertype,types,hp,images,set,tcgplayer'},
            headers=headers,
            timeout=8
        )
        r.raise_for_status()
        return jsonify(r.json())
    except Exception as e:
        return jsonify({'error': str(e), 'data': [], 'totalCount': 0}), 502


@app.route('/api/cards/quick-add', methods=['POST'])
@login_required
def quick_add_card():
    """Save a card selected from the TCG API picker."""
    data = request.get_json(force=True)
    if not data or not data.get('name'):
        return jsonify({'ok': False, 'error': 'No card data'}), 400

    card = Card(user_id=current_user.id)
    card.name           = data.get('name', '')
    card.card_number    = data.get('card_number', '')
    card.set_name       = data.get('set_name', '')
    card.set_code       = data.get('set_code', '')
    card.rarity         = data.get('rarity', '')
    card.card_type      = data.get('card_type', 'Pokemon')
    card.pokemon_type   = data.get('pokemon_type', '')
    card.hp             = data.get('hp')
    card.image_url      = data.get('image_url', '')
    card.quantity       = int(data.get('quantity', 1))
    card.purchase_price = data.get('purchase_price')
    card.market_price   = data.get('market_price')
    card.is_foil        = bool(data.get('is_foil', False))
    card.variant        = data.get('variant') or detect_variant(card.name, card.rarity, card.is_foil)
    card.is_graded      = bool(data.get('is_graded', False))
    card.grade          = data.get('grade')
    card.notes          = data.get('notes', '')
    if card.market_price:
        card.last_price_update = datetime.utcnow()

    db.session.add(card)
    db.session.commit()
    return jsonify({'ok': True, 'redirect': url_for('view_card', card_id=card.id)})
