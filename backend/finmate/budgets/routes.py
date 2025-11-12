from flask import jsonify, request

from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.finmate.budgets import bp
from .service import BudgetService




service = BudgetService()


@bp.route('/', methods=['GET'])
@jwt_required()
def get_all_budgets():
    try:
        user_id = int(get_jwt_identity())
        data = service.get_all_budgets_with_stats(user_id)
        return jsonify(data), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500


@bp.route('/', methods=['POST'])
@jwt_required()
def create_or_update_budget():
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()
        budget = service.create_or_update_budget(user_id, data)
        return jsonify(budget.to_dict()), 201

    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    except PermissionError as e:
        return jsonify({"error": str(e)}), 403

    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500


@bp.route('/<int:budget_id>', methods=['DELETE'])
@jwt_required()
def delete_budget(budget_id):
    try:
        user_id = int(get_jwt_identity())
        service.delete_budget(user_id, budget_id)
        return '', 204

    except ValueError as e:
        return jsonify({"error": str(e)}), 404

    except PermissionError as e:
        return jsonify({"error": str(e)}), 403

    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500