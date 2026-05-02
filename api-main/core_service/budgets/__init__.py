from flask import Blueprint

bp = Blueprint('budget', __name__)

from core_service.budgets import routes
