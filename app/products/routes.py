"""
ShopKart - Products Routes
Handles product listing, detail, search/filter, orders, and feedback.
"""
from flask import render_template, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import or_

from app import db
from app.models import Product, Order, Feedback
from app.products import products

PER_PAGE = 20


# ── HTML Pages ────────────────────────────────────────────────────────────────
@products.route('/')

def index():
    """Main product grid page."""
    return render_template('index.html')


@products.route('/products/<int:product_id>')
def detail(product_id):
    """Product detail page."""
    product = Product.query.get_or_404(product_id)
    return render_template('products/detail.html', product=product)


# ── API: Product Listing ──────────────────────────────────────────────────────
@products.route('/api/products')
def api_products():
    """
    GET /api/products
    Query params: page, q (search), category, min_price, max_price,
                  min_rating, sort (price_asc|price_desc|rating_desc|rating_asc)
    Returns paginated product list.
    """
    page       = request.args.get('page', 1, type=int)
    search     = request.args.get('q', '').strip()
    category   = request.args.get('category', '').strip()
    min_price  = request.args.get('min_price',  type=float)
    max_price  = request.args.get('max_price',  type=float)
    min_rating = request.args.get('min_rating', type=float)
    sort       = request.args.get('sort', 'default')

    q = Product.query

    # Full-text search across name, category, and description
    if search:
        like = f'%{search}%'
        q = q.filter(or_(
            Product.name.ilike(like),
            Product.category.ilike(like),
            Product.sub_category.ilike(like),
            Product.about_product.ilike(like),
        ))

    if category:
        q = q.filter(or_(
            Product.category.ilike(f'%{category}%'),
            Product.sub_category.ilike(f'%{category}%'),
        ))

    if min_price is not None:
        q = q.filter(Product.price >= min_price)
    if max_price is not None:
        q = q.filter(Product.price <= max_price)
    if min_rating is not None:
        q = q.filter(Product.rating >= min_rating)

    # Sorting
    sort_map = {
        'name_asc':    Product.name.asc(),
        'name_desc':   Product.name.desc(),
        'price_asc':   Product.price.asc(),
        'price_desc':  Product.price.desc(),
        'rating_desc': Product.rating.desc(),
        'rating_asc':  Product.rating.asc(),
        'popular':     Product.rating_count.desc(),
    }
    q = q.order_by(sort_map.get(sort, Product.id.asc()))

    total = q.count()
    items = q.offset((page - 1) * PER_PAGE).limit(PER_PAGE).all()

    return jsonify({
        'products': [p.to_dict() for p in items],
        'total':    total,
        'page':     page,
        'per_page': PER_PAGE,
        'pages':    max(1, (total + PER_PAGE - 1) // PER_PAGE),
    })


# ── API: Single Product + Recommendations ────────────────────────────────────
@products.route('/api/products/<int:product_id>')
@login_required
def api_product_detail(product_id):
    """
    GET /api/products/<id>
    Returns product data, its reviews, and 5 recommendations.
    """
    product = Product.query.get_or_404(product_id)

    # Latest 12 reviews
    reviews = (Feedback.query
               .filter_by(product_id=product_id)
               .order_by(Feedback.created_at.desc())
               .limit(12).all())

    # Recommendations: same category, highest rated
    recs = (Product.query
            .filter(Product.category == product.category,
                    Product.id != product_id)
            .order_by(Product.rating.desc())
            .limit(6).all())

    # Has the current user already reviewed?
    user_review = Feedback.query.filter_by(
        user_id=current_user.id, product_id=product_id).first()

    return jsonify({
        'product':         product.to_dict(),
        'extra_data':      product.get_extra_data(),
        'feedback':        [f.to_dict() for f in reviews],
        'recommendations': [p.to_dict() for p in recs],
        'user_review':     user_review.to_dict() if user_review else None,
    })


# ── API: Categories List ──────────────────────────────────────────────────────
@products.route('/api/categories')
@login_required
def api_categories():
    rows = (db.session.query(Product.category)
            .distinct()
            .filter(Product.category.isnot(None), Product.category != '')
            .order_by(Product.category)
            .all())
    return jsonify([r[0] for r in rows])


# ── API: Orders ───────────────────────────────────────────────────────────────
@products.route('/api/orders', methods=['GET'])
@login_required
def get_orders():
    """Return the logged-in user's orders (newest first)."""
    orders = (Order.query
              .filter_by(user_id=current_user.id)
              .order_by(Order.date.desc())
              .all())
    return jsonify([o.to_dict() for o in orders])


@products.route('/api/orders', methods=['POST'])
@login_required
def place_order():
    """Place a new order for a product."""
    data       = request.get_json(silent=True) or {}
    product_id = data.get('product_id')
    quantity   = max(1, int(data.get('quantity', 1)))

    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    order = Order(
        user_id     = current_user.id,
        product_id  = product_id,
        quantity    = quantity,
        total_price = round(product.price * quantity, 2),
        status      = 'pending',
    )
    db.session.add(order)
    db.session.commit()
    return jsonify({'success': True, 'order': order.to_dict()})


# ── API: Feedback ─────────────────────────────────────────────────────────────
@products.route('/api/feedback', methods=['GET'])
@login_required
def get_feedback():
    product_id = request.args.get('product_id', type=int)
    if not product_id:
        return jsonify({'error': 'product_id is required'}), 400
    reviews = (Feedback.query
               .filter_by(product_id=product_id)
               .order_by(Feedback.created_at.desc())
               .all())
    return jsonify([f.to_dict() for f in reviews])


@products.route('/api/feedback', methods=['POST'])
@login_required
def add_feedback():
    """Add or update the current user's review for a product."""
    data       = request.get_json(silent=True) or {}
    product_id = data.get('product_id')
    comment    = data.get('comment', '').strip()
    rating     = int(data.get('rating', 5))

    if not product_id or not comment:
        return jsonify({'error': 'product_id and comment are required'}), 400
    if not 1 <= rating <= 5:
        return jsonify({'error': 'rating must be between 1 and 5'}), 400

    existing = Feedback.query.filter_by(
        user_id=current_user.id, product_id=product_id).first()

    if existing:
        existing.comment = comment
        existing.rating  = rating
    else:
        existing = Feedback(user_id=current_user.id, product_id=product_id,
                            comment=comment, rating=rating)
        db.session.add(existing)

    db.session.commit()
    return jsonify({'success': True, 'feedback': existing.to_dict()})
