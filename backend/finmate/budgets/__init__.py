from flask import Blueprint

bp = Blueprint('budget', __name__)

from backend.finmate.budgets import routes
