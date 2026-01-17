from flask import Blueprint

bp = Blueprint('categories', __name__)

from . import routes