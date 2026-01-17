from flask import Blueprint

bp = Blueprint('profile', __name__)

from finmate.profile import routes