import os
from os import getenv

from dotenv import load_dotenv
from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy



db = SQLAlchemy()
login_manager = LoginManager()


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
    db.init_app(app)
    migrate = Migrate(app, db)

    login_manager.init_app(app)
    @login_manager.user_loader
    def load_user(user_id):
        from .models import Users
        return Users.query.get(user_id)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    from .auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from .core import bp as core_bp
    app.register_blueprint(core_bp)

    from .profile import bp as profile_bp
    app.register_blueprint(profile_bp, url_prefix='/profile')

    from .transactions import bp as trans_bp
    app.register_blueprint(trans_bp, url_prefix='/transaction')

    from .budgets import bp as budget_bp
    app.register_blueprint(budget_bp, url_prefix='/budgets')


    from . import models
    return app
