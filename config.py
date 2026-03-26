"""
ShopKart - Application Configuration
"""
import os

# Base directory of the project (where config.py lives)
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'shopkart-secret-key-2024-change-in-prod'

    # Database
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'instance', 'ecommerce.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Pagination
    PRODUCTS_PER_PAGE = 20

    # Dataset file path (place amazon.csv here)
    DATA_FILE = os.path.join(basedir, 'data', 'amazon.csv')

    DEBUG = True
