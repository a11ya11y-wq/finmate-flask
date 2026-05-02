from flask import Blueprint

bp = Blueprint('auth', __name__)

from core_service.auth import routes