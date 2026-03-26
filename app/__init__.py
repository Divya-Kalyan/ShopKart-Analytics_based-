"""
ShopKart - Application Factory
Creates and configures the Flask app with extensions and blueprints.
"""
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# ── Extensions (created here, initialised inside create_app) ──────────────────
db = SQLAlchemy()
login_manager = LoginManager()


def create_app():
    """Application factory – call this to get a configured Flask app."""
    app = Flask(
        __name__,
        template_folder='../templates',   # ecommerce/templates/
        static_folder='static',           # ecommerce/app/static/
    )

    # Load config
    from config import Config
    app.config.from_object(Config)

    # Ensure instance directory exists (for SQLite DB)
    os.makedirs(os.path.join(app.root_path, '..', 'instance'), exist_ok=True)

    # Initialise extensions
    db.init_app(app)

    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please sign in to access this page.'
    login_manager.login_message_category = 'warning'

    # Register blueprints ─────────────────────────────────────────────────────
    from app.auth import auth as auth_bp
    app.register_blueprint(auth_bp)

    from app.products import products as products_bp
    app.register_blueprint(products_bp)

    from app.admin import admin as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')

    from app.analytics import analytics_bp
    app.register_blueprint(analytics_bp)

    # Database setup ──────────────────────────────────────────────────────────
    with app.app_context():
        db.create_all()
        _seed_database(app)

    return app


def _seed_database(app):
    """Create default admin user and load product data on first run."""
    from app.models import User, Product
    from werkzeug.security import generate_password_hash

    # Default admin account
    if not User.query.filter_by(role='admin').first():
        admin = User(
            name='Admin',
            email='admin@shopkart.com',
            password=generate_password_hash('admin123'),
            role='admin',
        )
        db.session.add(admin)
        db.session.commit()
        print('✔  Default admin created → admin@shopkart.com / admin123')

    # Load product catalogue
    if Product.query.count() == 0:
        from app.data_loader import load_data
        print('⏳  Loading product data (first run) …')
        load_data(app)
        print(f'✔  Products loaded: {Product.query.count():,}')
