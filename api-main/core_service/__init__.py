import os

from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS
import redis
import logging


load_dotenv()

from .extensions import db, migrate, jwt, redis_client, init_redis, init_celery, init_limiter
from .utils.error_handlers import register_error_handlers
from .config import config

FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format=FORMAT)


def create_app(config_name='default'):
    app = Flask(__name__)

    app.config.from_object(config[config_name])
    app.config['ENCRYPTION_KEY'] = app.config['ENCRYPTION_KEY'].encode('utf-8')


    app.config['CORS_HEADERS'] = 'Content-Type,Authorization'
    allowed_origins = [
        'http://localhost:5173',
        'http://127.0.0.1:5173',
        'http://127.0.0.1:5000',
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]

    env_origins = os.environ.get("CORS_ORIGINS")
    if env_origins:
        allowed_origins.extend(env_origins.split(","))

    CORS(app, resources={r"/api/*": {"origins": allowed_origins}}, supports_credentials=True)

    app.url_map.strict_slashes = False

    jwt.init_app(app)
    db.init_app(app)
    init_celery(app)
    init_limiter(app)
    register_error_handlers(app)
    migrate.init_app(app, db)
    init_redis(app)

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

        from .reports import bp as report_bp
        app.register_blueprint(mono_bp, url_prefix='/api/v1/report')


        from . import models

    return app
