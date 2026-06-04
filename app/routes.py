import os
import uuid
from collections import defaultdict
from datetime import datetime
from flask import render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import text
from werkzeug.utils import secure_filename

from app import app, db
from app.models import User, Card, CardCatalog, SealedItem, SealedCatalog, RipSession, RipSessionCard
from app.forms import LoginForm, RegisterForm, CardForm, EditCardForm, SearchForm, ALL_SETS, ALL_SETS_JA, ALL_SETS_KO, shorten_set_name

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
    cards  = current_user.cards.order_by(Card.added_at.desc()).all()
    sealed = current_user.sealed_items.order_by(SealedItem.added_at.desc()).all()

    total_cards    = len(cards)
    unique_pokemon = len(set(c.name.lower() for c in cards))
    sealed_count   = sum(s.quantity for s in sealed)

    total_value = (sum((c.market_price or 0) * c.quantity for c in cards)
                 + sum((s.market_price or 0) * s.quantity for s in sealed))
    total_cost  = (sum((c.purchase_price or 0) * c.quantity for c in cards)
                 + sum((s.purchase_price or 0) * s.quantity for s in sealed))
    has_cost    = any(c.purchase_price for c in cards) or any(s.purchase_price for s in sealed)
    profit_loss = (total_value - total_cost) if has_cost else None

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
                           sealed=sealed,
                           total_cards=total_cards,
                           unique_pokemon=unique_pokemon,
                           sealed_count=sealed_count,
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

    # ── Group same physical cards together (same name + set + number) ──────
    groups_dict = {}
    group_order = []
    for card in cards:
        # Graded cards are always their own standalone entry
        if card.is_graded:
            key = ('__graded__', card.id)
        else:
            key = (card.name, card.set_code or '', card.card_number or '')
        if key not in groups_dict:
            groups_dict[key] = {'card': card, 'variants': defaultdict(int)}
            group_order.append(key)
        else:
            rep = groups_dict[key]['card']
            # Prefer a card row that actually has an image
            if (card.image_url or card.local_image) and not (rep.image_url or rep.local_image):
                groups_dict[key]['card'] = card
        variant_label = card.variant or 'Standard'
        groups_dict[key]['variants'][variant_label] += (card.quantity or 1)

    card_groups = []
    for key in group_order:
        g = groups_dict[key]
        variants = [{'label': k, 'qty': v} for k, v in g['variants'].items()]
        card_groups.append({
            'card':     g['card'],
            'variants': variants,
            'total':    sum(v['qty'] for v in variants),
        })

    total_copies = sum(g['total'] for g in card_groups)

    rarities = db.session.query(Card.rarity).filter(
        Card.user_id == current_user.id, Card.rarity != None
    ).distinct().all()
    rarities = [r[0] for r in rarities]

    return render_template('collection.html',
                           title='My Collection',
                           card_groups=card_groups,
                           total_copies=total_copies,
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
                   .filter(CardCatalog.name.ilike(f'%{q}%'))
                   .order_by(_SET_AGE_EXPR, _NUM_EXPR, CardCatalog.card_number)
                   .limit(200)
                   .all())
        if results:
            owned_rows = (db.session.query(Card.name, Card.set_code)
                          .filter(Card.user_id == current_user.id,
                                  Card.name.ilike(f'%{q}%'))
                          .all())
            owned_keys = {(r.name.lower(), r.set_code) for r in owned_rows}

    return render_template('search.html', title='Search',
                           results=results, owned_keys=owned_keys, query=q)


# ─── Card CRUD ───────────────────────────────────────────────────────────────

def _era_for(code):
    _PROMOS = {'svp','swshp','smp','xyp','bwp','hsp','dpp','np','basep','bp',
               'pop1','pop2','pop3','pop4','pop5','pop6','pop7','pop8','pop9',
               'mcd11','mcd12','mcd14','mcd15','mcd16','mcd17','mcd18','mcd19',
               'mcd21','mcd22','ru1','fut20'}
    if code in _PROMOS:                                              return 'promo'
    if code.startswith('me'):                                        return 'me'
    if code.startswith('swsh') or code in ('cel25', 'pgo'):         return 'swsh'
    if code.startswith('sv') or code.startswith('rsv') or code.startswith('zsv'): return 'sv'
    if code.startswith('sm') or code in ('sm35','det1'):            return 'sm'
    if code.startswith('xy') or code in ('dc1','g1'):               return 'xy'
    if code.startswith('bw') or code == 'dv1':                      return 'bw'
    if code.startswith('hgss') or code == 'col1':                   return 'hgss'
    if code.startswith('dp') or code.startswith('pl'):              return 'dp'
    if code.startswith('ex'):                                        return 'ex'
    if code.startswith('neo') or code in ('si1','base6','ecard1','ecard2','ecard3'):
                                                                     return 'neo'
    if code.startswith('base') or code.startswith('gym'):           return 'base'
    return 'other'

@app.route('/card/add')
@login_required
def add_card():
    short_sets    = [(code, shorten_set_name(label)) for code, label in ALL_SETS]
    set_eras      = {code: _era_for(code) for code, _ in ALL_SETS}
    return render_template('add_card.html', title='Add Card',
                           all_sets=short_sets, set_eras=set_eras,
                           all_sets_ja=ALL_SETS_JA, all_sets_ko=ALL_SETS_KO)


@app.route('/card/<int:card_id>')
@login_required
def view_card(card_id):
    card = Card.query.get_or_404(card_id)
    if card.user_id != current_user.id and not current_user.is_admin():
        abort(403)

    # Fetch all versions of this card the user owns (same name + set + number)
    siblings = Card.query.filter_by(
        user_id=card.user_id,
        name=card.name,
        set_code=card.set_code or '',
        card_number=card.card_number or '',
    ).all()

    # Build variant breakdown — {label: total_qty}
    variant_map = defaultdict(int)
    for s in siblings:
        variant_map[s.variant or 'Standard'] += (s.quantity or 1)
    variants = [{'label': k, 'qty': v} for k, v in variant_map.items()]
    total_copies = sum(v['qty'] for v in variants)

    # Find every rip session where this exact card was pulled
    rip_q = (db.session.query(RipSession)
             .join(RipSessionCard, RipSession.id == RipSessionCard.session_id)
             .filter(
                 RipSession.user_id == current_user.id,
                 db.func.lower(RipSessionCard.name) == card.name.lower(),
             ))
    if card.set_code:
        rip_q = rip_q.filter(RipSessionCard.set_code == card.set_code)
    if card.card_number:
        rip_q = rip_q.filter(RipSessionCard.card_number == card.card_number)
    rip_sources = rip_q.order_by(RipSession.ripped_at.desc()).all()

    return render_template('view_card.html', title=card.name, card=card,
                           variants=variants, total_copies=total_copies,
                           rip_sources=rip_sources)


@app.route('/card/<int:card_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_card(card_id):
    card = Card.query.get_or_404(card_id)
    if card.user_id != current_user.id and not current_user.is_admin():
        abort(403)

    # All versions of this card the user owns (same name + set + number)
    siblings = Card.query.filter_by(
        user_id=card.user_id,
        name=card.name,
        set_code=card.set_code or '',
        card_number=card.card_number or '',
    ).order_by(Card.id).all()

    form = EditCardForm(obj=card)
    if form.validate_on_submit():
        card.notes          = form.notes.data
        card.purchase_price = form.purchase_price.data
        card.updated_at     = datetime.utcnow()

        # Update / delete each sibling based on submitted quantities
        deleted_current = False
        for sibling in siblings:
            new_qty = request.form.get(f'qty_{sibling.id}', type=int)
            if new_qty is None:
                continue
            if new_qty <= 0:
                if sibling.id == card.id:
                    deleted_current = True
                db.session.delete(sibling)
            else:
                sibling.quantity    = new_qty
                sibling.updated_at  = datetime.utcnow()

        db.session.commit()
        flash(f'"{card.name}" updated.', 'success')

        if deleted_current:
            survivor = Card.query.filter_by(
                user_id=current_user.id,
                name=card.name,
                set_code=card.set_code or '',
                card_number=card.card_number or '',
            ).first()
            return redirect(url_for('view_card', card_id=survivor.id) if survivor
                            else url_for('collection'))

        return redirect(url_for('view_card', card_id=card.id))

    return render_template('card_form.html', title='Edit Card',
                           form=form, card=card, siblings=siblings, action='edit')


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
    lang     = request.args.get('lang',     '').strip().upper()  # 'JA' or ''
    page     = max(int(request.args.get('page', 1) or 1), 1)
    page_size = min(int(request.args.get('pageSize', 20) or 20), 100)

    catalog_total = CardCatalog.query.count()

    has_filter = bool(name or set_code or number or era or lang)
    if not has_filter:
        return jsonify({'data': [], 'totalCount': 0,
                        'catalogEmpty': catalog_total == 0})

    q = CardCatalog.query

    if name:
        q = q.filter(CardCatalog.name.ilike(f'%{name}%'))
    if set_code:
        q = q.filter(CardCatalog.set_code == set_code)
    if number:
        q = q.filter(CardCatalog.card_number.ilike(f'{number}%'))
    if era and not set_code:
        q = q.filter(CardCatalog.era == era)
    # Scope to the correct language catalog when no specific set_code is given.
    if lang == 'JA' and not set_code:
        q = q.filter(CardCatalog.era.like('ja-%'))
    if lang == 'KO' and not set_code:
        q = q.filter(CardCatalog.era.like('ko-%'))

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
    card.is_xl          = bool(data.get('is_xl', False))
    card.language       = data.get('language', 'EN') or 'EN'
    card.notes          = data.get('notes', '')
    if card.market_price:
        card.last_price_update = datetime.utcnow()

    db.session.add(card)
    db.session.commit()
    return jsonify({'ok': True, 'redirect': url_for('view_card', card_id=card.id)})


# ─── Sealed Items ─────────────────────────────────────────────────────────────

@app.route('/api/sealed/refresh-prices', methods=['POST'])
@login_required
def refresh_sealed_prices():
    """
    For every sealed item owned by the current user, look up the matching
    SealedCatalog entry by name and copy its cached market_price.
    Returns JSON: { ok, updated, missing }
    """
    items   = current_user.sealed_items.all()
    updated = 0
    missing = 0

    for item in items:
        # Match by exact name to the catalog (case-insensitive for safety)
        cat = SealedCatalog.query.filter(
            db.func.lower(SealedCatalog.name) == item.name.lower()
        ).first()

        if cat and cat.market_price:
            item.market_price      = cat.market_price
            item.last_price_update = datetime.utcnow()
            updated += 1
        else:
            missing += 1

    db.session.commit()
    return jsonify({'ok': True, 'updated': updated, 'missing': missing})


ITEM_TYPES = [
    'Booster Pack', 'Blister Pack', 'Booster Box', 'Elite Trainer Box',
    'Super Premium Collection', 'Premium Collection', 'Collection Box',
    'Tin', 'Bundle', 'Gift Box', 'Other',
]

@app.route('/sealed')
@login_required
def sealed_collection():
    sort        = request.args.get('sort', 'recent')
    filter_type = request.args.get('type', '')

    query = current_user.sealed_items
    if filter_type:
        query = query.filter(SealedItem.item_type == filter_type)

    if sort == 'name':
        query = query.order_by(SealedItem.name)
    elif sort == 'value':
        query = query.order_by(SealedItem.market_price.desc().nullslast())
    elif sort == 'type':
        query = query.order_by(SealedItem.item_type, SealedItem.name)
    else:
        query = query.order_by(SealedItem.added_at.desc())

    items = query.all()

    item_types = [t[0] for t in db.session.query(SealedItem.item_type)
                  .filter(SealedItem.user_id == current_user.id,
                          SealedItem.item_type != None)
                  .distinct().all()]

    total_qty   = sum(s.quantity for s in items)
    total_value = sum((s.market_price or 0) * s.quantity for s in items)

    return render_template('sealed_collection.html',
                           title='Sealed Items',
                           items=items,
                           item_types=item_types,
                           current_sort=sort,
                           current_type=filter_type,
                           total_qty=total_qty,
                           total_value=total_value)


@app.route('/sealed/add')
@login_required
def add_sealed():
    short_sets = [(code, shorten_set_name(label)) for code, label in ALL_SETS]
    item_types = SealedCatalog.query.with_entities(SealedCatalog.item_type).distinct().order_by(SealedCatalog.item_type).all()
    item_types = [r[0] for r in item_types]
    return render_template('add_sealed.html', title='Add Item',
                           all_sets=short_sets, item_types=item_types,
                           all_sets_ja=ALL_SETS_JA)


@app.route('/api/sealed-catalog')
@login_required
def sealed_catalog_search():
    set_code  = request.args.get('set_code', '').strip()
    item_type = request.args.get('item_type', '').strip()
    name      = request.args.get('name', '').strip()

    q = SealedCatalog.query
    if set_code:
        # Match the primary set OR any secondary set in the comma-padded set_codes field.
        # set_codes is stored as ",sv1,sv2," so we search for ",sv1,"
        padded = f',{set_code},'
        q = q.filter(
            db.or_(
                SealedCatalog.set_code == set_code,
                SealedCatalog.set_codes.like(f'%{padded}%'),
            )
        )
    if item_type: q = q.filter(SealedCatalog.item_type == item_type)
    if name:      q = q.filter(SealedCatalog.name.ilike(f'%{name}%'))

    items = q.order_by(SealedCatalog.item_type, SealedCatalog.name).all()
    return jsonify({'data': [i.to_dict() for i in items], 'total': len(items)})


@app.route('/api/sealed/quick-add', methods=['POST'])
@login_required
def sealed_quick_add():
    data = request.get_json(force=True)
    if not data or not data.get('name'):
        return jsonify({'ok': False, 'error': 'No item data'}), 400

    item = SealedItem(user_id=current_user.id)
    item.name           = data['name']
    item.item_type      = data.get('item_type', '')
    item.set_name       = data.get('set_name', '')
    item.set_code       = data.get('set_code', '')
    item.image_url      = data.get('image_url', '')
    item.quantity       = max(1, int(data.get('quantity', 1) or 1))
    pp = data.get('purchase_price')
    mp = data.get('market_price')
    item.purchase_price = float(pp) if pp else None
    item.market_price   = float(mp) if mp else None
    item.notes          = data.get('notes', '')
    item.language       = data.get('language', 'EN') or 'EN'
    item.is_opened      = bool(data.get('is_opened', False))

    db.session.add(item)
    db.session.commit()
    return jsonify({'ok': True, 'redirect': url_for('view_sealed', item_id=item.id)})


@app.route('/rip')
@login_required
def rip_center():
    """Legacy URL — redirect to the Items collection."""
    return redirect(url_for('sealed_collection'))


@app.route('/sealed/<int:item_id>/rip')
@login_required
def rip_pack(item_id):
    item = SealedItem.query.get_or_404(item_id)
    if item.user_id != current_user.id and not current_user.is_admin():
        abort(403)
    if item.item_type != 'Booster Pack':
        flash('Only Booster Packs can be ripped.', 'warning')
        return redirect(url_for('view_sealed', item_id=item_id))
    if item.quantity < 1:
        flash('No packs left to rip!', 'warning')
        return redirect(url_for('view_sealed', item_id=item_id))
    pack_era = _era_for(item.set_code or '')
    return render_template('rip_pack.html', title='Rip Pack', item=item, pack_era=pack_era)


@app.route('/sealed/<int:item_id>/build')
@login_required
def build_item(item_id):
    """Open a non-booster-pack sealed item by adding its contents manually."""
    item = SealedItem.query.get_or_404(item_id)
    if item.user_id != current_user.id and not current_user.is_admin():
        abort(403)
    if item.item_type == 'Booster Pack':
        return redirect(url_for('rip_pack', item_id=item_id))
    if item.quantity < 1:
        flash('No items left to open!', 'warning')
        return redirect(url_for('view_sealed', item_id=item_id))
    return render_template('build_item.html', title=f'Open — {item.name}', item=item)


@app.route('/api/sealed/<int:item_id>/complete-build', methods=['POST'])
@login_required
def complete_build(item_id):
    """Add the contents of a non-pack sealed item to the user's collection."""
    item = SealedItem.query.get_or_404(item_id)
    if item.user_id != current_user.id and not current_user.is_admin():
        abort(403)

    data        = request.get_json(force=True)
    packs_data  = data.get('packs',  [])
    promos_data = data.get('promos', [])

    if not packs_data and not promos_data:
        return jsonify({'ok': False, 'error': 'Nothing added — select packs or promo cards first.'}), 400

    # Add packs to the user's sealed items
    for p in packs_data:
        sealed           = SealedItem(user_id=current_user.id)
        sealed.name      = p.get('name', '').strip()
        sealed.item_type = p.get('item_type', 'Booster Pack').strip()
        sealed.set_name  = p.get('set_name', '').strip()
        sealed.set_code  = p.get('set_code', '').strip()
        sealed.image_url = p.get('image_url', '').strip()
        sealed.quantity  = max(1, int(p.get('quantity', 1) or 1))
        db.session.add(sealed)

    # Add promo cards to the collection
    for cd in promos_data:
        card             = Card(user_id=current_user.id)
        card.name        = cd.get('name', '').strip()
        card.card_number = cd.get('card_number', '').strip()
        card.set_name    = cd.get('set_name', '').strip()
        card.set_code    = cd.get('set_code', '').strip()
        card.rarity      = cd.get('rarity', '').strip()
        card.image_url   = cd.get('image_url', '').strip()
        card.quantity    = 1
        card.variant     = cd.get('variant') or detect_variant(card.name, card.rarity)
        card.is_foil     = 'holo' in (card.rarity or '').lower()
        card.card_type   = 'Pokémon'

        if card.set_code and card.card_number:
            cat = CardCatalog.query.filter_by(
                set_code=card.set_code, card_number=card.card_number
            ).first()
            if cat and cat.market_price:
                card.market_price      = cat.market_price
                card.last_price_update = datetime.utcnow()

        db.session.add(card)

    # Consume one of the parent item
    item.quantity -= 1
    if item.quantity <= 0:
        db.session.delete(item)
    else:
        item.updated_at = datetime.utcnow()

    db.session.commit()

    parts = []
    if packs_data:
        n = len(packs_data)
        parts.append(f'{n} pack{"s" if n != 1 else ""} added to your Items')
    if promos_data:
        n = len(promos_data)
        parts.append(f'{n} promo card{"s" if n != 1 else ""} added to your collection')
    flash('Opened! ' + ' · '.join(parts) + '.', 'success')
    return jsonify({'ok': True, 'redirect': url_for('sealed_collection')})


@app.route('/api/sealed/<int:item_id>/complete-rip', methods=['POST'])
@login_required
def complete_rip(item_id):
    item = SealedItem.query.get_or_404(item_id)
    if item.user_id != current_user.id and not current_user.is_admin():
        abort(403)
    if item.item_type != 'Booster Pack':
        return jsonify({'ok': False, 'error': 'Not a booster pack'}), 400

    data       = request.get_json(force=True)
    cards_data = data.get('cards', [])
    if not cards_data:
        return jsonify({'ok': False, 'error': 'No cards provided'}), 400

    # ── Record the rip session ───────────────────────────────────────────────
    rip = RipSession(
        user_id        = current_user.id,
        pack_name      = item.name,
        pack_set_name  = item.set_name,
        pack_set_code  = item.set_code,
        pack_image_url = item.image_url,
        card_count     = len(cards_data),
        ripped_at      = datetime.utcnow(),
    )
    db.session.add(rip)
    db.session.flush()   # assigns rip.id before we reference it below

    for cd in cards_data:
        card             = Card(user_id=current_user.id)
        card.name        = cd.get('name', '').strip()
        card.card_number = cd.get('card_number', '').strip()
        card.set_name    = cd.get('set_name', '').strip()
        card.set_code    = cd.get('set_code', '').strip()
        card.rarity      = cd.get('rarity', '').strip()
        card.image_url   = cd.get('image_url', '').strip()
        card.quantity    = 1
        card.variant     = cd.get('variant') or detect_variant(card.name, card.rarity)
        card.is_foil        = 'holo' in (card.rarity or '').lower()
        card.card_type      = 'Pokémon'
        card.rip_session_id = rip.id   # links this card back to its rip session

        # Pull market price from the local catalog if indexed
        if card.set_code and card.card_number:
            cat = CardCatalog.query.filter_by(
                set_code=card.set_code,
                card_number=card.card_number
            ).first()
            if cat and cat.market_price:
                card.market_price      = cat.market_price
                card.last_price_update = datetime.utcnow()

        db.session.add(card)

        # Mirror into the rip session log
        rc = RipSessionCard(
            session_id  = rip.id,
            name        = card.name,
            card_number = card.card_number,
            set_name    = card.set_name,
            set_code    = card.set_code,
            rarity      = card.rarity,
            variant     = card.variant,
            image_url   = card.image_url,
        )
        db.session.add(rc)

    # Consume one pack. If that was the last one, remove the item entirely.
    item.quantity -= 1
    if item.quantity <= 0:
        db.session.delete(item)
    else:
        item.updated_at = datetime.utcnow()

    db.session.commit()

    n = len(cards_data)
    flash(f'Pack ripped! {n} card{"s" if n != 1 else ""} added to your collection.', 'success')
    return jsonify({'ok': True, 'cards_added': n, 'redirect': url_for('view_rip', rip_id=rip.id)})


@app.route('/sealed/<int:item_id>')
@login_required
def view_sealed(item_id):
    item = SealedItem.query.get_or_404(item_id)
    if item.user_id != current_user.id and not current_user.is_admin():
        abort(403)
    return render_template('view_sealed.html', title=item.name, item=item)


@app.route('/sealed/<int:item_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_sealed(item_id):
    item = SealedItem.query.get_or_404(item_id)
    if item.user_id != current_user.id and not current_user.is_admin():
        abort(403)
    if request.method == 'POST':
        item.purchase_price = float(p) if (p := request.form.get('purchase_price', '').strip()) else None
        item.market_price   = float(p) if (p := request.form.get('market_price', '').strip()) else None
        item.is_opened      = bool(request.form.get('is_opened'))
        item.notes          = request.form.get('notes', '').strip()
        new_qty = request.form.get('quantity', type=int)
        if new_qty is not None and new_qty >= 1:
            item.quantity = new_qty
        item.updated_at     = datetime.utcnow()
        db.session.commit()
        flash(f'"{item.name}" updated.', 'success')
        return redirect(url_for('view_sealed', item_id=item.id))
    return render_template('edit_sealed.html', title='Edit Item', item=item)


@app.route('/sealed/<int:item_id>/delete', methods=['POST'])
@login_required
def delete_sealed(item_id):
    item = SealedItem.query.get_or_404(item_id)
    if item.user_id != current_user.id and not current_user.is_admin():
        abort(403)
    name = item.name
    db.session.delete(item)
    db.session.commit()
    flash(f'"{name}" removed from your collection.', 'info')
    return redirect(url_for('sealed_collection'))


# ─── Rip History ─────────────────────────────────────────────────────────────

@app.route('/rips')
@login_required
def rip_history():
    """List all past rip sessions for the current user."""
    sessions = (RipSession.query
                .filter_by(user_id=current_user.id)
                .order_by(RipSession.ripped_at.desc())
                .all())
    return render_template('rip_history.html', title='Rip History', sessions=sessions)


@app.route('/rips/<int:rip_id>')
@login_required
def view_rip(rip_id):
    """Show every card pulled in a single rip session."""
    rip = RipSession.query.get_or_404(rip_id)
    if rip.user_id != current_user.id and not current_user.is_admin():
        abort(403)
    cards = rip.cards.all()
    return render_template('view_rip.html',
                           title=f'Pack Rip — {rip.pack_name}',
                           rip=rip, cards=cards)


@app.route('/rips/<int:rip_id>/delete', methods=['POST'])
@login_required
def delete_rip(rip_id):
    """Delete a rip session and every card that was pulled from it."""
    rip = RipSession.query.get_or_404(rip_id)
    if rip.user_id != current_user.id and not current_user.is_admin():
        abort(403)

    pack_name = rip.pack_name

    # Remove all collection cards that were added by this rip
    deleted = Card.query.filter_by(
        user_id        = current_user.id,
        rip_session_id = rip_id,
    ).delete(synchronize_session=False)

    # Remove the session itself (cascades to rip_session_cards automatically)
    db.session.delete(rip)
    db.session.commit()

    flash(
        f'"{pack_name}" rip deleted — {deleted} card{"s" if deleted != 1 else ""} '
        f'removed from your collection.',
        'info',
    )
    return redirect(url_for('rip_history'))
