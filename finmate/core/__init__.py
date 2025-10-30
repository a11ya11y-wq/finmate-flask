from flask import Blueprint

bp = Blueprint('core', __name__)

from finmate.core import routes