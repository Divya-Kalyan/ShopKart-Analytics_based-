"""
ShopKart - Authentication Routes
Handles customer login/signup and admin login.
"""
from flask import render_template, request, redirect, url_for, jsonify, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from app import db
from app.models import User
from app.auth import auth


# ── Helper ────────────────────────────────────────────────────────────────────
def _is_json():
    return request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest'


# ── Customer Login ────────────────────────────────────────────────────────────
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('products.index'))

    if request.method == 'POST':
        data     = request.get_json() if _is_json() else request.form
        email    = data.get('email', '').strip().lower()
        password = data.get('password', '')

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            if user.role == 'admin':
                err = 'Please use the Admin Login page.'
                if _is_json():
                    return jsonify({'error': err}), 403
                flash(err, 'warning')
                return redirect(url_for('auth.admin_login'))

            login_user(user, remember=True)
            nxt = request.args.get('next') or url_for('products.index')
            if _is_json():
                return jsonify({'success': True, 'redirect': nxt})
            return redirect(nxt)

        err = 'Invalid email or password.'
        if _is_json():
            return jsonify({'error': err}), 401
        flash(err, 'danger')

    return render_template('auth/login.html')


# ── Customer Signup ───────────────────────────────────────────────────────────
@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('products.index'))

    if request.method == 'POST':
        data     = request.get_json() if _is_json() else request.form
        name     = data.get('name', '').strip()
        email    = data.get('email', '').strip().lower()
        password = data.get('password', '')

        # Validation
        if not name or not email or not password:
            err = 'All fields are required.'
            if _is_json(): return jsonify({'error': err}), 400
            flash(err, 'danger')
            return render_template('auth/signup.html')

        if len(password) < 6:
            err = 'Password must be at least 6 characters.'
            if _is_json(): return jsonify({'error': err}), 400
            flash(err, 'danger')
            return render_template('auth/signup.html')

        if User.query.filter_by(email=email).first():
            err = 'Email is already registered.'
            if _is_json(): return jsonify({'error': err}), 400
            flash(err, 'danger')
            return render_template('auth/signup.html')

        user = User(name=name, email=email,
                    password=generate_password_hash(password), role='customer')
        db.session.add(user)
        db.session.commit()

        login_user(user, remember=True)
        if _is_json():
            return jsonify({'success': True, 'redirect': url_for('products.index')})
        return redirect(url_for('products.index'))

    return render_template('auth/signup.html')


# ── Logout ────────────────────────────────────────────────────────────────────
@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('products.index'))


# ── Admin Login ───────────────────────────────────────────────────────────────
@auth.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated and current_user.role == 'admin':
        return redirect(url_for('admin.dashboard'))

    if request.method == 'POST':
        data     = request.get_json() if _is_json() else request.form
        email    = data.get('email', '').strip().lower()
        password = data.get('password', '')

        user = User.query.filter_by(email=email, role='admin').first()

        if user and check_password_hash(user.password, password):
            login_user(user, remember=True)
            if _is_json():
                return jsonify({'success': True, 'redirect': url_for('admin.dashboard')})
            return redirect(url_for('admin.dashboard'))

        err = 'Invalid admin credentials.'
        if _is_json():
            return jsonify({'error': err}), 401
        flash(err, 'danger')

    return render_template('auth/admin_login.html')
