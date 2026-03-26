"""
ShopKart - Database Models
Defines all SQLAlchemy ORM models used across the application.
"""
import json
from datetime import datetime
from app import db, login_manager
from flask_login import UserMixin


# ── User Loader (required by Flask-Login) ─────────────────────────────────────
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ──────────────────────────────────────────────────────────────────────────────
# Product
# ──────────────────────────────────────────────────────────────────────────────
class Product(db.Model):
    __tablename__ = 'products'

    id                  = db.Column(db.Integer, primary_key=True)
    product_id          = db.Column(db.String(60))          # original dataset ID
    name                = db.Column(db.String(500), nullable=False)
    category            = db.Column(db.String(200), index=True)
    sub_category        = db.Column(db.String(200))
    price               = db.Column(db.Float, default=0.0)  # discounted / current price
    actual_price        = db.Column(db.Float, default=0.0)  # MRP / original price
    discount_percentage = db.Column(db.String(20))
    rating              = db.Column(db.Float, default=0.0)
    rating_count        = db.Column(db.Integer, default=0)
    about_product       = db.Column(db.Text)
    img_link            = db.Column(db.String(1000))
    product_link        = db.Column(db.String(1000))
    extra_data          = db.Column(db.Text)                # JSON blob for remaining CSV cols
    created_at          = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    orders   = db.relationship('Order',    backref='product', lazy=True, cascade='all, delete-orphan')
    feedback = db.relationship('Feedback', backref='product', lazy=True, cascade='all, delete-orphan')

    # ── Helpers ───────────────────────────────────────────────────────────────
    @property
    def image_url(self):
        """Return a usable image URL, falling back to a placeholder."""
        if self.img_link and self.img_link.startswith('http'):
            return self.img_link
        # Deterministic placeholder based on product id
        seed = self.id or 1
        return f'https://picsum.photos/seed/{seed}/400/400'

    def get_extra_data(self):
        """Parse the JSON extra_data field."""
        if self.extra_data:
            try:
                return json.loads(self.extra_data)
            except (ValueError, TypeError):
                return {}
        return {}

    def to_dict(self):
        return {
            'id':                  self.id,
            'product_id':          self.product_id,
            'name':                self.name,
            'category':            self.category or '',
            'sub_category':        self.sub_category or '',
            'price':               self.price,
            'actual_price':        self.actual_price,
            'discount_percentage': self.discount_percentage or '',
            'rating':              self.rating,
            'rating_count':        self.rating_count,
            'about_product':       self.about_product or '',
            'img_link':            self.image_url,
            'product_link':        self.product_link or '',
        }

    def __repr__(self):
        return f'<Product {self.id}: {self.name[:40]}>'


# ──────────────────────────────────────────────────────────────────────────────
# User
# ──────────────────────────────────────────────────────────────────────────────
class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(100), nullable=False)
    email      = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password   = db.Column(db.String(200), nullable=False)
    role       = db.Column(db.String(20), default='customer')   # customer | admin
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    orders   = db.relationship('Order',    backref='user', lazy=True, cascade='all, delete-orphan')
    feedback = db.relationship('Feedback', backref='user', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id':         self.id,
            'name':       self.name,
            'email':      self.email,
            'role':       self.role,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M'),
        }

    def __repr__(self):
        return f'<User {self.id}: {self.email}>'


# ──────────────────────────────────────────────────────────────────────────────
# Order
# ──────────────────────────────────────────────────────────────────────────────
class Order(db.Model):
    __tablename__ = 'orders'

    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('users.id'),    nullable=False)
    product_id  = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity    = db.Column(db.Integer, default=1)
    total_price = db.Column(db.Float)
    status      = db.Column(db.String(50), default='pending')  # pending|processing|shipped|delivered
    date        = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            'id':           self.id,
            'user_id':      self.user_id,
            'user_name':    self.user.name  if self.user    else 'Unknown',
            'product_id':   self.product_id,
            'product_name': self.product.name if self.product else 'Unknown',
            'quantity':     self.quantity,
            'total_price':  self.total_price,
            'status':       self.status,
            'date':         self.date.strftime('%Y-%m-%d %H:%M'),
        }

    def __repr__(self):
        return f'<Order {self.id}>'


# ──────────────────────────────────────────────────────────────────────────────
# Feedback / Review
# ──────────────────────────────────────────────────────────────────────────────
class Feedback(db.Model):
    __tablename__ = 'feedback'

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'),    nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    comment    = db.Column(db.Text)
    rating     = db.Column(db.Integer)   # 1 – 5
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id':         self.id,
            'user_id':    self.user_id,
            'user_name':  self.user.name if self.user else 'Anonymous',
            'product_id': self.product_id,
            'comment':    self.comment,
            'rating':     self.rating,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M'),
        }

    def __repr__(self):
        return f'<Feedback {self.id}>'


# ──────────────────────────────────────────────────────────────────────────────
# Employee
# ──────────────────────────────────────────────────────────────────────────────
class Employee(db.Model):
    __tablename__ = 'employees'

    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(100), nullable=False)
    email      = db.Column(db.String(150))
    role       = db.Column(db.String(50))
    department = db.Column(db.String(50))
    salary     = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id':         self.id,
            'name':       self.name,
            'email':      self.email or '',
            'role':       self.role or '',
            'department': self.department or '',
            'salary':     self.salary,
            'created_at': self.created_at.strftime('%Y-%m-%d'),
        }

    def __repr__(self):
        return f'<Employee {self.id}: {self.name}>'
