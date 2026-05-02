from flask import Blueprint

bp = Blueprint('transactions', __name__)

from core_service.transactions import routes