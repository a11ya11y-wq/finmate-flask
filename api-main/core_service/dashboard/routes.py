from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from core_service.dashboard.service import DashboardService
from core_service.utils.error_parser import parse_exception
from core_service.uow import UnitOfWork
from . import bp


@bp.route('/')
@jwt_required()
def get_dashboard():
    period = request.args.get('period', 'all')
    user_id = int(get_jwt_identity())
    try:
        with UnitOfWork() as uow:
            service = DashboardService(uow)
            data = service.get_dashboard_data(user_id, period)
            
        return jsonify(data), 200
    
    except Exception as e:
        return parse_exception(e)


@bp.route('/history')
@jwt_required()
def get_transaction_history():
    user_id = int(get_jwt_identity())
    period = request.args.get('period', 'all')
    page = request.args.get('page', 1, type=int)
    try:
        with UnitOfWork() as uow:
            service = DashboardService(uow)
            data = service.get_tx_history(user_id, period, page)

        return jsonify(data), 200

    except Exception as e:
        return parse_exception(e)
