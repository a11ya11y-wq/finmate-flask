from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager


load_dotenv()

from .config import config
from .db import db

migrate = Migrate()
jwt = JWTManager()

def create_app(config_name='default'):
    app = Flask(__name__)

    app.config.from_object(config[config_name])
    app.config['ENCRYPTION_KEY'] = app.config['ENCRYPTION_KEY'].encode('utf-8')

    # <-- COPILOT -->
    app.config['CORS_HEADERS'] = 'Content-Type,Authorization'
    # Allow dev frontend origins explicitly and enable credentials (so Authorization header/cookies work)
    allowed_origins = [
        'http://localhost:5173',
        'http://127.0.0.1:5173',
        # include backend origin for same-origin requests in production if needed
        'http://127.0.0.1:5000',
    ]
    CORS(app, resources={r"/api/*": {"origins": allowed_origins}}, supports_credentials=True)

    # Disable strict slashes to avoid automatic redirects (which break CORS preflight OPTIONS)
    app.url_map.strict_slashes = False

    jwt.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)

    with app.app_context():
        from .categories import bp as cat_bp
        app.register_blueprint(cat_bp, url_prefix='/api/v1/categories')

        from .profile import bp as profile_bp
        app.register_blueprint(profile_bp, url_prefix='/api/v1/profile')

        from .budgets import bp as budget_bp
        app.register_blueprint(budget_bp, url_prefix='/api/v1/budgets')

        from .dashboard import bp as dash_bp
        app.register_blueprint(dash_bp, url_prefix='/api/v1/dashboard')

        from .transactions import bp as tx_bp
        app.register_blueprint(tx_bp, url_prefix='/api/v1/transactions')

        from .auth import bp as auth_bp
        app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')

        from .monobank import bp as mono_bp
        app.register_blueprint(mono_bp, url_prefix='/api/v1/monobank')

        from . import models

    return app
