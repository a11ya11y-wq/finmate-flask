from flask import Blueprint

bp = Blueprint("monobank",__name__)

from backend.finmate.monobank import routes