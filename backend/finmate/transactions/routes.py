from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from . import bp
from .service import TransactionService
from finmate.utils.error_parser import parse_exception

service = TransactionService()


@bp.route('/', methods=['POST'])
@jwt_required()
def create_transaction():
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()
        new_tx = service.create_transaction(data, user_id)
        return jsonify(new_tx.to_dict()), 201

    except Exception as e:
        return parse_exception(e)


@bp.route('/<int:tx_id>', methods=['DELETE'])
@jwt_required()
def delete_transaction(tx_id):
    try:
        user_id = int(get_jwt_identity())
        service.delete_transaction(tx_id, user_id)
        return '', 204

    except Exception as e:
        return parse_exception(e)


@bp.route('/<int:tx_id>', methods=['PUT'])
@jwt_required()
def update_transaction(tx_id):
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()
        updated_tx = service.update_transaction(tx_id, user_id, data)
        return jsonify(updated_tx.to_dict()), 200

    except Exception as e:
        return parse_exception(e)


@bp.route('/<int:tx_id>', methods=['GET'])
@jwt_required()
def get_transaction(tx_id):
    try:
        user_id = int(get_jwt_identity())
        transaction = service.get_transaction(tx_id, user_id)
        return jsonify(transaction.to_dict()), 200

    except Exception as e:
        return parse_exception(e)
