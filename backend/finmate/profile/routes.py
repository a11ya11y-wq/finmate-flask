from flask_jwt_extended import jwt_required, get_jwt_identity
from flask import request, jsonify
from backend.finmate.profile import bp
from .service import ProfileService



service = ProfileService()


@bp.route('/me', methods=['GET'])
@jwt_required()
def get_user_profile():
    try:
        user_id = int(get_jwt_identity())
        user = service.get_user_info(user_id)
        return jsonify(user.to_dict()), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500


@bp.route('/me', methods=['PUT'])
@jwt_required()
def update_user():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    try:
        updated_user = service.update_user(user_id, data)
        return jsonify(updated_user.to_dict()), 200

    except ValueError as e:
        status_code = 404 if "not found" in str(e).lower() else 400 #TODO: Кастом ексепшн зробити (UserNotFound, ValidationError)
        return jsonify({"error": str(e)}), status_code

    except PermissionError as e:
        return jsonify({"error": str(e)}), 403

    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500


@bp.route('/me', methods=['DELETE'])
@jwt_required()
def delete_account():
    user_id = int(get_jwt_identity())
    try:
        service.delete_user(user_id)
        return '', 204

    except ValueError as e:
        return jsonify({"error": str(e)}), 404

    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500


@bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()

        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        service.change_password(user_id, data)
        return jsonify({"message": "Password updated successfully"}), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500


@bp.route('/monobank', methods=['PUT'])
@jwt_required()
def update_monobank_integration():
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()

        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        updated_user= service.update_mono_token(user_id, data)
        return jsonify(updated_user.to_dict()), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500


@bp.route('/monobank', methods=['DELETE'])
@jwt_required()
def delete_monobank_token():
    try:
        user_id = int(get_jwt_identity())
        service.delete_mono_token(user_id)
        return '', 204

    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500



