from flask import Blueprint

bp = Blueprint('budget', __name__)

from finmate.budgets import routes
