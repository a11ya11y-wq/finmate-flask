from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from core_service.profile import bp
from core_service.utils.error_parser import parse_exception
from core_service.utils.permissions import prevent_demo_user
from .service import ProfileService
from core_service.uow import UnitOfWork


@bp.route('/me', methods=['GET'])
@jwt_required()
def get_user_profile():
    user_id = int(get_jwt_identity())
    try:
        with UnitOfWork() as uow:
            service = ProfileService(uow)
            user = service.get_user_data(user_id)

        return jsonify(user), 200
    except Exception as e:
        return parse_exception(e)


@bp.route('/me', methods=['PUT'])
@jwt_required()
@prevent_demo_user
def update_user():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    try:
        with UnitOfWork() as uow:
            service = ProfileService(uow)
            updated_user = service.update_user(user_id, data)
            response_data = updated_user.to_dict()

        return jsonify(response_data), 200

    except Exception as e:
        return parse_exception(e)


@bp.route('/me', methods=['DELETE'])
@jwt_required()
@prevent_demo_user
def delete_account():
    user_id = int(get_jwt_identity())
    try:
        with UnitOfWork() as uow:
            service = ProfileService(uow)
            service.delete_user(user_id)

        return '', 204

    except Exception as e:
        return parse_exception(e)


@bp.route('/change-password', methods=['POST'])
@jwt_required()
@prevent_demo_user
def change_password():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    try:
        with UnitOfWork() as uow:
            service = ProfileService(uow)
            service.change_password(user_id, data)

        return jsonify({"message": "Password updated successfully"}), 200

    except Exception as e:
        return parse_exception(e)


@bp.route('/monobank', methods=['PUT'])
@jwt_required()
def update_monobank_integration():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    try:
        with UnitOfWork() as uow:
            service = ProfileService(uow)
            updated_user = service.update_mono_token(user_id, data)
            response_data = updated_user.to_dict()
            
        return jsonify(response_data), 200

    except Exception as e:
        return parse_exception(e)


@bp.route('/monobank', methods=['DELETE'])
@jwt_required()
def delete_monobank_token():
    user_id = int(get_jwt_identity())
    try:
        with UnitOfWork() as uow:
            service = ProfileService(uow)
            service.delete_mono_token(user_id)
        return '', 204

    except Exception as e:
        return parse_exception(e)
