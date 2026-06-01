from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from core_service.budgets import bp
from core_service.utils.error_parser import parse_exception
from .service import BudgetService
from core_service.uow import UnitOfWork



@bp.route('/', methods=['GET'])
@jwt_required()
def get_all_budgets():
    user_id = int(get_jwt_identity())
    try:
        with UnitOfWork() as uow:
            service = BudgetService(uow)
            data = service.get_all_budgets_with_stats(user_id)

        return jsonify(data), 200

    except Exception as e:
        return parse_exception(e)


@bp.route('/', methods=['POST'])
@jwt_required()
def create_or_update_budget():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    try:
        with UnitOfWork() as uow:
            service = BudgetService(uow)
            budget, is_created = service.create_or_update_budget(user_id, data)
            response_data = budget.to_dict()
        status_code = 201 if is_created else 200

        return jsonify(response_data), status_code

    except Exception as e:
        return parse_exception(e)


@bp.route('/<int:budget_id>', methods=['DELETE'])
@jwt_required()
def delete_budget(budget_id: int):
    user_id = int(get_jwt_identity())
    try:
        with UnitOfWork() as uow:
            service = BudgetService(uow)
            service.delete_budget(user_id, budget_id)
            
        return '', 204

    except Exception as e:
        return parse_exception(e)
