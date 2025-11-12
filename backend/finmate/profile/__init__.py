from flask import Blueprint

bp = Blueprint('profile', __name__)

from backend.finmate.profile import routes