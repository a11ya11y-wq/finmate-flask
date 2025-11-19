from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from .service import CategoryService
from  . import bp
from backend.finmate.exceptions import ConflictError


service = CategoryService()

@bp.route('/all', methods=['GET'])
@jwt_required()
def get_all_categories():
    user_id = int(get_jwt_identity())
    try:
        categories = service.get_all_categories(user_id)
        return jsonify([cat.to_dict() for cat in categories]), 200

    except ValueError as e:
        status_code = 404 if "not found" in str(e).lower() else 400
        return jsonify({"error": str(e)}), status_code

    except PermissionError as e:
        return jsonify({"error": str(e)}), 403


    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500


@bp.route('/', methods=['POST'])
@jwt_required()
def create_category():
    user_id = int(get_jwt_identity())
    data = request.get_json()

    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    try:
        new_cat = service.create_category(user_id, data)
        return jsonify(new_cat.to_dict()), 201

    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    except PermissionError as e:
        return jsonify({"error": str(e)}), 403

    except ConflictError as e:
        return jsonify({"error": str(e)}), ConflictError.status_code

    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500


@bp.route('/<int:cat_id>', methods=['PUT'])
@jwt_required()
def update_category(cat_id):
    user_id = int(get_jwt_identity())
    data = request.get_json()

    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    try:
        updated_cat = service.update_category(user_id, data, cat_id)
        return jsonify(updated_cat.to_dict()), 200

    except ValueError as e:
        status_code = 404 if "not found" in str(e).lower() else 400
        return jsonify({"error": str(e)}), status_code

    except PermissionError as e:
        return jsonify({"error": str(e)}), 403

    except FileExistsError as e:
        return jsonify({"error": str(e)}), 409

    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500


@bp.route('/<int:cat_id>', methods=['DELETE'])
@jwt_required()
def delete_category(cat_id):
    user_id = int(get_jwt_identity())
    try:
        service.delete_category(cat_id, user_id)
        return '', 204
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

    except PermissionError as e:
        return jsonify({"error": str(e)}), 403

    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500



