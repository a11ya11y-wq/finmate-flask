from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from finmate.profile import bp
from finmate.utils.error_parser import parse_exception
from .service import ProfileService

service = ProfileService()


@bp.route('/me', methods=['GET'])
@jwt_required()
def get_user_profile():
    try:
        user_id = int(get_jwt_identity())
        user = service.get_user_data(user_id)
        return jsonify(user), 200
    except Exception as e:
        return parse_exception(e)


@bp.route('/me', methods=['PUT'])
@jwt_required()
def update_user():
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()
        updated_user = service.update_user(user_id, data)
        return jsonify(updated_user.to_dict()), 200

    except Exception as e:
        return parse_exception(e)


@bp.route('/me', methods=['DELETE'])
@jwt_required()
def delete_account():
    try:
        user_id = int(get_jwt_identity())
        service.delete_user(user_id)
        return '', 204

    except Exception as e:
        return parse_exception(e)


@bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()

        service.change_password(user_id, data)
        return jsonify({"message": "Password updated successfully"}), 200

    except Exception as e:
        return parse_exception(e)


@bp.route('/monobank', methods=['PUT'])
@jwt_required()
def update_monobank_integration():
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()

        updated_user = service.update_mono_token(user_id, data)
        return jsonify(updated_user.to_dict()), 200

    except Exception as e:
        return parse_exception(e)


@bp.route('/monobank', methods=['DELETE'])
@jwt_required()
def delete_monobank_token():
    try:
        user_id = int(get_jwt_identity())
        service.delete_mono_token(user_id)
        return '', 204

    except Exception as e:
        return parse_exception(e)
