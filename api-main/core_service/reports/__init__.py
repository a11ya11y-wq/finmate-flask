from flask import Blueprint

bp = Blueprint('report', __name__)

from core_service.reports import routes