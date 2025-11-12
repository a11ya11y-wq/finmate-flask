from flask import Blueprint

bp = Blueprint('auth', __name__)

from backend.finmate.auth import routes