from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from . import bp
from backend.finmate.dashboard.service import DashboardService

dashboard_service = DashboardService()



@bp.route('/')
@jwt_required()
def get_dashboard():

    period = request.args.get('period', 'all')
    user_id = int(get_jwt_identity())

    try:
        data = dashboard_service.get_dashboard_data(user_id, period)
        return jsonify(data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500