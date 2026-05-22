from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='collector')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    cards = db.relationship('Card', backref='owner', lazy='dynamic', cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == 'admin'

    @property
    def collection_value(self):
        return sum(c.market_price or 0 for c in self.cards)

    @property
    def card_count(self):
        return self.cards.count()

    def __repr__(self):
        return f'<User {self.username}>'


class SetReference(db.Model):
    """Master list of every TCG set — used to populate form dropdowns."""
    __tablename__ = 'set_references'

    id       = db.Column(db.Integer, primary_key=True)
    name     = db.Column(db.String(120), nullable=False)
    code     = db.Column(db.String(20),  unique=True, nullable=False)
    era      = db.Column(db.String(50))   # "XY", "Sun & Moon", etc.
    year     = db.Column(db.Integer)

    def __repr__(self):
        return f'<Set {self.code} – {self.name}>'


class Card(db.Model):
    __tablename__ = 'cards'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    name         = db.Column(db.String(100), nullable=False)
    card_number  = db.Column(db.String(20))
    set_name     = db.Column(db.String(100))
    set_code     = db.Column(db.String(20))
    rarity       = db.Column(db.String(50))
    card_type    = db.Column(db.String(50))
    hp           = db.Column(db.Integer)
    pokemon_type = db.Column(db.String(30))

    condition    = db.Column(db.String(20), default='NM')
    quantity     = db.Column(db.Integer, default=1)
    is_foil      = db.Column(db.Boolean, default=False)
    is_graded    = db.Column(db.Boolean, default=False)
    grade        = db.Column(db.String(10))

    purchase_price    = db.Column(db.Float)
    market_price      = db.Column(db.Float)
    last_price_update = db.Column(db.DateTime)

    image_url    = db.Column(db.String(500))
    local_image  = db.Column(db.String(200))

    notes      = db.Column(db.Text)
    added_at   = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Card {self.name} {self.card_number}>'

    @property
    def display_image(self):
        if self.local_image:
            return f'/static/uploads/{self.local_image}'
        if self.image_url:
            return self.image_url
        return '/static/placeholder.png'

    @property
    def profit_loss(self):
        if self.purchase_price and self.market_price:
            return (self.market_price - self.purchase_price) * self.quantity
        return None
