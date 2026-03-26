from flask import Blueprint, render_template, jsonify, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import func
from app.models import Product
from app import db
import datetime
import random

# DEFINE BLUEPRINT FIRST (VERY IMPORTANT)
analytics_bp = Blueprint('analytics', __name__, url_prefix='/admin/analytics')


# PROTECT ALL ROUTES (ADMIN ONLY)
@analytics_bp.before_request
@login_required
def require_admin():
    if current_user.role != 'admin':
        return redirect(url_for('auth.login'))


# ── PAGE ─────────────────────────────────────────────
@analytics_bp.route('/')
def index():
    return render_template('admin/analytics.html')


# ── API: CATEGORY ────────────────────────────────────
@analytics_bp.route('/api/category-distribution')
def category_distribution():
    results = (
        db.session.query(Product.category, func.count(Product.id).label('count'))
        .filter(Product.category.isnot(None))
        .group_by(Product.category)
        .order_by(func.count(Product.id).desc())
        .all()
    )
    return jsonify([{'category': r.category, 'count': r.count} for r in results])


# ── API: PRICE ───────────────────────────────────────
@analytics_bp.route('/api/price-distribution')
def price_distribution():
    ranges = [
        ('Under $10', 0, 10),
        ('$10 - $25', 10, 25),
        ('$25 - $50', 25, 50),
        ('$50 - $100', 50, 100),
        ('$100 - $250', 100, 250),
        ('Over $250', 250, float('inf')),
    ]

    data = []
    for label, low, high in ranges:
        if high == float('inf'):
            count = Product.query.filter(Product.price >= low).count()
        else:
            count = Product.query.filter(Product.price >= low, Product.price < high).count()
        data.append({'range': label, 'count': count})

    return jsonify(data)


# ── API: RATING ──────────────────────────────────────
@analytics_bp.route('/api/rating-distribution')
def rating_distribution():
    ranges = [
        ('0 - 1', 0, 1),
        ('1 - 2', 1, 2),
        ('2 - 3', 2, 3),
        ('3 - 4', 3, 4),
        ('4 - 5', 4, 5),
    ]

    data = []
    for label, low, high in ranges:
        if high == 5:
            count = Product.query.filter(Product.rating >= low, Product.rating <= high).count()
        else:
            count = Product.query.filter(Product.rating >= low, Product.rating < high).count()
        data.append({'range': label, 'count': count})

    return jsonify(data)


# ── API: TOP PRODUCTS ────────────────────────────────
@analytics_bp.route('/api/top-products')
def top_products():
    products = (
        Product.query
        .filter(Product.rating.isnot(None))
        .order_by(Product.rating.desc(), Product.rating_count.desc())
        .limit(10)
        .all()
    )

    return jsonify([
        {
            'id': p.id,
            'name': p.name,
            'category': p.category or '',
            'price': p.price,
            'rating': p.rating,
            'rating_count': p.rating_count,
            'img_link': p.image_url,
        }
        for p in products
    ])

# ── KPI DATA ─────────────────────────────────────────
@analytics_bp.route('/api/kpis')
def kpis():
    total_products = Product.query.count()
    total_categories = db.session.query(Product.category).distinct().count()
    total_revenue = db.session.query(func.sum(Product.price)).scalar() or 0
    avg_rating = db.session.query(func.avg(Product.rating)).scalar() or 0

    return jsonify({
        "total_products": total_products,
        "total_categories": total_categories,
        "total_revenue": float(total_revenue),
        "avg_rating": float(avg_rating)
    })


# ── SALES TREND (FAKE FOR NOW BUT WORKING) ───────────
import datetime
import random

@analytics_bp.route('/api/sales-trend')
def sales_trend():
    dates = []
    counts = []

    for i in range(30):
        day = datetime.date.today() - datetime.timedelta(days=29 - i)
        dates.append(day.strftime('%d %b'))
        counts.append(random.randint(5, 25))  # fake data

    return jsonify({
        "dates": dates,
        "counts": counts
    })