from flask import Blueprint

bp = Blueprint('categories', __name__)

from backend.finmate.categories import routes