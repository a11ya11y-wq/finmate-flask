from flask import Blueprint

bp = Blueprint("monobank",__name__)

from core_service.monobank import routes