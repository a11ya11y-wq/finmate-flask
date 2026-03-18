from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from finmate.dashboard.service import DashboardService
from finmate.utils.error_parser import parse_exception
from . import bp

dashboard_service = DashboardService()


@bp.route('/')
@jwt_required()
def get_dashboard():
    try:
        period = request.args.get('period', 'all')
        user_id = int(get_jwt_identity())
        data = dashboard_service.get_dashboard_data(user_id, period)
        return jsonify(data), 200
    except Exception as e:
        return parse_exception(e)
