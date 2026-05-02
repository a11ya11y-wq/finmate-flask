from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from core_service.utils.error_parser import parse_exception
from . import bp
from .service import CategoryService

service = CategoryService()


@bp.route('/all', methods=['GET'])
@jwt_required()
def get_all_categories():
    try:
        user_id = int(get_jwt_identity())
        categories_data = service.get_all_categories(user_id)
        return jsonify({"data": categories_data}), 200

    except Exception as e:
        return parse_exception(e)


@bp.route('/', methods=['POST'])
@jwt_required()
def create_category():
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()
        new_cat = service.create_category(user_id, data)
        return jsonify(new_cat.to_dict()), 201

    except Exception as e:
        return parse_exception(e)


@bp.route('/<int:cat_id>', methods=['PUT'])
@jwt_required()
def update_category(cat_id: int):
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()
        updated_cat = service.update_category(user_id, data, cat_id)
        return jsonify(updated_cat.to_dict()), 200

    except Exception as e:
        return parse_exception(e)


@bp.route('/<int:cat_id>', methods=['DELETE'])
@jwt_required()
def delete_category(cat_id: int):
    try:
        user_id = int(get_jwt_identity())
        service.delete_category(cat_id, user_id)
        return '', 204

    except Exception as e:
        return parse_exception(e)
