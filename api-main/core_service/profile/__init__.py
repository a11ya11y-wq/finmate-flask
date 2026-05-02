from flask import Blueprint

bp = Blueprint('profile', __name__)

from core_service.profile import routes