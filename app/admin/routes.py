"""
ShopKart - Admin Routes
All routes require admin role. Exposes HTML pages + JSON API endpoints.
"""
from functools import wraps
from flask import render_template, request, jsonify, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import func
from datetime import datetime, timedelta

from app import db
from app.models import Product, User, Order, Feedback, Employee
from app.admin import admin


# ── Admin Guard Decorator ─────────────────────────────────────────────────────
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            if request.path.startswith('/admin/api/'):
                return jsonify({'error': 'Admin access required'}), 403
            return redirect(url_for('auth.admin_login'))
        return f(*args, **kwargs)
    return decorated


# ── HTML Pages ────────────────────────────────────────────────────────────────
@admin.route('/')
@admin.route('/dashboard')
@login_required
@admin_required
def dashboard():
    return render_template('admin/dashboard.html')

@admin.route('/products')
@login_required
@admin_required
def products_page():
    return render_template('admin/products.html')

@admin.route('/users')
@login_required
@admin_required
def users_page():
    return render_template('admin/users.html')

@admin.route('/employees')
@login_required
@admin_required
def employees_page():
    return render_template('admin/employees.html')

@admin.route('/orders')
@login_required
@admin_required
def orders_page():
    return render_template('admin/orders.html')

@admin.route('/feedback')
@login_required
@admin_required
def feedback_page():
    return render_template('admin/feedback.html')


# ── API: Dashboard Stats ──────────────────────────────────────────────────────
@admin.route('/api/stats')
@login_required
@admin_required
def api_stats():
    total_products = Product.query.count()
    total_users    = User.query.filter_by(role='customer').count()
    total_orders   = Order.query.count()
    total_revenue  = db.session.query(func.sum(Order.total_price)).scalar() or 0

    # New this month
    start_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0)
    new_orders     = Order.query.filter(Order.date >= start_of_month).count()
    new_users      = User.query.filter(
        User.created_at >= start_of_month, User.role == 'customer').count()

    return jsonify({
        'total_products': total_products,
        'total_users':    total_users,
        'total_orders':   total_orders,
        'total_revenue':  round(float(total_revenue), 2),
        'new_orders':     new_orders,
        'new_users':      new_users,
    })


@admin.route('/api/chart/orders_over_time')
@login_required
@admin_required
def chart_orders_over_time():
    """Orders and revenue for the last 30 days."""
    start = datetime.utcnow() - timedelta(days=29)
    rows  = (db.session.query(
                 func.date(Order.date).label('d'),
                 func.count(Order.id).label('cnt'),
                 func.sum(Order.total_price).label('rev'))
             .filter(Order.date >= start)
             .group_by(func.date(Order.date))
             .order_by(func.date(Order.date))
             .all())
    return jsonify({
        'dates':    [str(r.d)   for r in rows],
        'counts':   [r.cnt      for r in rows],
        'revenues': [round(float(r.rev or 0), 2) for r in rows],
    })


@admin.route('/api/chart/categories')
@login_required
@admin_required
def chart_categories():
    """Product count per top-10 category."""
    rows = (db.session.query(Product.category, func.count(Product.id).label('c'))
            .group_by(Product.category)
            .order_by(func.count(Product.id).desc())
            .limit(10).all())
    return jsonify({'categories': [r[0] for r in rows], 'counts': [r[1] for r in rows]})


# ── API: Products CRUD ────────────────────────────────────────────────────────
@admin.route('/api/products')
@login_required
@admin_required
def api_products():
    page    = request.args.get('page', 1, type=int)
    per     = 15
    search  = request.args.get('q', '').strip()
    q       = Product.query
    if search:
        q = q.filter(Product.name.ilike(f'%{search}%'))
    total   = q.count()
    items   = q.order_by(Product.id.desc()).offset((page - 1) * per).limit(per).all()
    return jsonify({
        'products': [p.to_dict() for p in items],
        'total':    total,
        'page':     page,
        'pages':    max(1, (total + per - 1) // per),
    })


# ── API: Single Product (by ID) ──────────────────────────────────────────────
@admin.route('/api/products/<int:pid>')
@login_required
@admin_required
def api_get_product(pid):
    """
    GET /admin/api/products/<pid>
    Returns the full details of one product as JSON.
    Used to pre-fill the Edit Product form in the admin panel.
    """
    # Fetch the product, or return 404 if it doesn't exist
    p = Product.query.get_or_404(pid)
    return jsonify({'product': p.to_dict()})


@admin.route('/api/products', methods=['POST'])
@login_required
@admin_required
def api_add_product():
    d = request.get_json(silent=True) or {}
    p = Product(
        product_id          = f'MANUAL_{Product.query.count() + 1}',
        name                = d.get('name', 'New Product')[:500],
        category            = d.get('category', '')[:200],
        sub_category        = d.get('sub_category', '')[:200],
        price               = float(d.get('price', 0)),
        actual_price        = float(d.get('actual_price', 0)),
        discount_percentage = str(d.get('discount_percentage', ''))[:20],
        rating              = float(d.get('rating', 0)),
        rating_count        = int(d.get('rating_count', 0)),
        about_product       = d.get('about_product', ''),
        img_link            = d.get('img_link', '')[:1000],
    )
    db.session.add(p)
    db.session.commit()
    return jsonify({'success': True, 'product': p.to_dict()})


@admin.route('/api/products/<int:pid>', methods=['PUT'])
@login_required
@admin_required
def api_update_product(pid):
    p = Product.query.get_or_404(pid)
    d = request.get_json(silent=True) or {}
    fields = ['name', 'category', 'sub_category', 'about_product', 'img_link',
              'discount_percentage']
    for f in fields:
        if f in d: setattr(p, f, d[f])
    for f in ['price', 'actual_price', 'rating']:
        if f in d: setattr(p, f, float(d[f]))
    if 'rating_count' in d: p.rating_count = int(d['rating_count'])
    db.session.commit()
    return jsonify({'success': True, 'product': p.to_dict()})


@admin.route('/api/products/<int:pid>', methods=['DELETE'])
@login_required
@admin_required
def api_delete_product(pid):
    p = Product.query.get_or_404(pid)
    db.session.delete(p)
    db.session.commit()
    return jsonify({'success': True})


# ── API: Users ────────────────────────────────────────────────────────────────
@admin.route('/api/users')
@login_required
@admin_required
def api_users():
    page  = request.args.get('page', 1, type=int)
    per   = 15
    q     = User.query.filter_by(role='customer')
    total = q.count()
    users = q.order_by(User.created_at.desc()).offset((page - 1) * per).limit(per).all()
    return jsonify({
        'users': [u.to_dict() for u in users],
        'total': total, 'page': page,
        'pages': max(1, (total + per - 1) // per),
    })


# ── API: Update User ─────────────────────────────────────────────────────────
@admin.route('/api/users/<int:uid>', methods=['PUT'])
@login_required
@admin_required
def api_update_user(uid):
    """
    PUT /admin/api/users/<uid>
    Updates a user's name, email, and/or role.
    Only the fields you include in the JSON body are changed.
    """
    u = User.query.get_or_404(uid)
    d = request.get_json(silent=True) or {}

    # --- Update name (if provided) ---
    if 'name' in d:
        name = d['name'].strip()
        if not name:
            return jsonify({'error': 'Name cannot be empty'}), 400
        u.name = name[:100]          # max 100 chars (matches the model)

    # --- Update email (if provided) ---
    if 'email' in d:
        email = d['email'].strip().lower()
        # Basic format check
        if not email or '@' not in email:
            return jsonify({'error': 'A valid email address is required'}), 400
        # Make sure no other account already uses this email
        taken = User.query.filter_by(email=email).first()
        if taken and taken.id != uid:
            return jsonify({'error': 'That email is already used by another account'}), 400
        u.email = email[:150]        # max 150 chars (matches the model)

    # --- Update role (if provided) ---
    if 'role' in d:
        role = d['role'].strip().lower()
        if role not in ('customer', 'admin'):
            return jsonify({'error': 'Role must be "customer" or "admin"'}), 400
        u.role = role

    db.session.commit()
    return jsonify({'success': True, 'user': u.to_dict()})


@admin.route('/api/users/<int:uid>', methods=['DELETE'])
@login_required
@admin_required
def api_delete_user(uid):
    u = User.query.get_or_404(uid)
    if u.role == 'admin':
        return jsonify({'error': 'Cannot delete admin account'}), 403
    db.session.delete(u)
    db.session.commit()
    return jsonify({'success': True})


# ── API: Employees CRUD ───────────────────────────────────────────────────────
@admin.route('/api/employees')
@login_required
@admin_required
def api_employees():
    employees = Employee.query.order_by(Employee.created_at.desc()).all()
    return jsonify([e.to_dict() for e in employees])


@admin.route('/api/employees', methods=['POST'])
@login_required
@admin_required
def api_add_employee():
    d = request.get_json(silent=True) or {}
    e = Employee(
        name       = d.get('name', ''),
        email      = d.get('email', ''),
        role       = d.get('role', ''),
        department = d.get('department', ''),
        salary     = float(d.get('salary', 0)),
    )
    db.session.add(e)
    db.session.commit()
    return jsonify({'success': True, 'employee': e.to_dict()})


@admin.route('/api/employees/<int:eid>', methods=['DELETE'])
@login_required
@admin_required
def api_delete_employee(eid):
    e = Employee.query.get_or_404(eid)
    db.session.delete(e)
    db.session.commit()
    return jsonify({'success': True})


# ── API: Orders ───────────────────────────────────────────────────────────────
@admin.route('/api/orders')
@login_required
@admin_required
def api_orders():
    page   = request.args.get('page', 1, type=int)
    per    = 15
    total  = Order.query.count()
    orders = (Order.query.order_by(Order.date.desc())
              .offset((page - 1) * per).limit(per).all())
    return jsonify({
        'orders': [o.to_dict() for o in orders],
        'total':  total, 'page': page,
        'pages':  max(1, (total + per - 1) // per),
    })


@admin.route('/api/orders/<int:oid>', methods=['PUT'])
@login_required
@admin_required
def api_update_order(oid):
    o = Order.query.get_or_404(oid)
    d = request.get_json(silent=True) or {}
    valid_statuses = ('pending', 'processing', 'shipped', 'delivered', 'cancelled')
    if 'status' in d and d['status'] in valid_statuses:
        o.status = d['status']
    db.session.commit()
    return jsonify({'success': True, 'order': o.to_dict()})


# ── API: Feedback ─────────────────────────────────────────────────────────────
@admin.route('/api/feedback')
@login_required
@admin_required
def api_feedback():
    page     = request.args.get('page', 1, type=int)
    per      = 15
    total    = Feedback.query.count()
    feedback = (Feedback.query.order_by(Feedback.created_at.desc())
                .offset((page - 1) * per).limit(per).all())
    return jsonify({
        'feedback': [f.to_dict() for f in feedback],
        'total':    total, 'page': page,
        'pages':    max(1, (total + per - 1) // per),
    })


@admin.route('/api/feedback/<int:fid>', methods=['DELETE'])
@login_required
@admin_required
def api_delete_feedback(fid):
    f = Feedback.query.get_or_404(fid)
    db.session.delete(f)
    db.session.commit()
    return jsonify({'success': True})
