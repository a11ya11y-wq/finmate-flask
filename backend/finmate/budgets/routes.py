from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from finmate.budgets import bp
from finmate.utils.error_parser import parse_exception
from .service import BudgetService

service = BudgetService()


@bp.route('/', methods=['GET'])
@jwt_required()
def get_all_budgets():
    try:
        user_id = int(get_jwt_identity())
        data = service.get_all_budgets_with_stats(user_id)
        return jsonify(data), 200

    except Exception as e:
        return parse_exception(e)


@bp.route('/', methods=['POST'])
@jwt_required()
def create_or_update_budget():
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()

        budget, is_created = service.create_or_update_budget(user_id, data)

        status_code = 201 if is_created else 200

        return jsonify(budget.to_dict()), 201

    except Exception as e:
        return parse_exception(e)


@bp.route('/<int:budget_id>', methods=['DELETE'])
@jwt_required()
def delete_budget(budget_id: int):
    try:
        user_id = int(get_jwt_identity())
        service.delete_budget(user_id, budget_id)
        return '', 204

    except Exception as e:
        return parse_exception(e)
