from flask import Blueprint

bp = Blueprint("monobank",__name__)

from finmate.monobank import routes