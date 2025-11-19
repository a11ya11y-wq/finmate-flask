from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from . import bp
from .service import TransactionService


service = TransactionService()


@bp.route('/', methods=['POST'])
@jwt_required()
def create_transaction():

    user_id = int(get_jwt_identity())
    data = request.get_json()

    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    try:
        new_tx = service.create_transaction(data, user_id)
        return jsonify(new_tx.to_dict()), 201

    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    except PermissionError as e:
        return jsonify({"error": str(e)}), 403

    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500


@bp.route('/<int:tx_id>', methods=['DELETE'])
@jwt_required()
def delete_transaction(tx_id):
    user_id = int(get_jwt_identity())
    try:
        service.delete_transaction(tx_id, user_id)
        return '', 204

    except ValueError as e:
        return jsonify({"error": str(e)}), 404

    except PermissionError as e:
        return jsonify({"error": str(e)}), 403

    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500


@bp.route('/<int:tx_id>', methods=['PUT'])
@jwt_required()
def update_transaction(tx_id):
    user_id = int(get_jwt_identity())
    data = request.get_json()

    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    try:
        updated_tx = service.update_transaction(tx_id, user_id, data)
        return jsonify(updated_tx.to_dict()), 200

    except ValueError as e:
        status_code = 404 if "not found" in str(e).lower() else 400
        return jsonify({"error": str(e)}), status_code

    except PermissionError as e:
        return jsonify({"error": str(e)}), 403

    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500


@bp.route('/<int:tx_id>', methods=['GET'])
@jwt_required()
def get_transaction(tx_id):
    user_id = int(get_jwt_identity())
    try:
        transaction = service.get_transaction(tx_id, user_id)
        return jsonify(transaction.to_dict()), 200

    except ValueError as e:
        status_code = 404 if "not found" in str(e).lower() else 400
        return jsonify({"error": str(e)}), status_code

    except PermissionError as e:
        return jsonify({"error": str(e)}), 403

    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500
