import os
from os import getenv

from dotenv import load_dotenv
from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager



db = SQLAlchemy()


# << Folder static/template >>
package_dir = os.path.abspath(os.path.dirname(__file__))

base_dir = os.path.dirname(package_dir)

template_folder = os.path.join(base_dir, 'templates')
static_folder = os.path.join(base_dir, 'static')


def create_app():
    app = Flask(__name__,
                template_folder=template_folder,
                static_folder=static_folder
                )

    load_dotenv()

    app.config['SQLALCHEMY_DATABASE_URI'] =  getenv('DATABASE_URL')
    app.config['SECRET_KEY'] = getenv('SECRET_KEY')
    app.config['ENCRYPTION_KEY'] = os.environ.get('ENCRYPTION_KEY').encode('utf-8')
    app.config['JWT_SECRET_KEY'] = getenv('JWT_SECRET_KEY')

    jwt = JWTManager(app)

    db.init_app(app)
    migrate = Migrate(app, db)

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


    from . import models
    return app
