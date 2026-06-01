from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from core_service.utils.error_parser import parse_exception
from . import bp
from .service import TransactionService
from core_service.uow import UnitOfWork


@bp.route('/', methods=['POST'])
@jwt_required()
def create_transaction():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    try:
        with UnitOfWork() as uow:
            service = TransactionService(uow)
            new_tx = service.create_transaction(data, user_id)
            response_data = new_tx.to_dict()
            
        return jsonify(response_data), 201

    except Exception as e:
        return parse_exception(e)


@bp.route('/<int:tx_id>', methods=['DELETE'])
@jwt_required()
def delete_transaction(tx_id: int):
    user_id = int(get_jwt_identity())
    try:
        with UnitOfWork() as uow:
            service = TransactionService(uow)
            service.delete_transaction(tx_id, user_id)

        return '', 204

    except Exception as e:
        return parse_exception(e)


@bp.route('/<int:tx_id>', methods=['PUT'])
@jwt_required()
def update_transaction(tx_id: int):
    user_id = int(get_jwt_identity())
    data = request.get_json()
    try:
        with UnitOfWork() as uow:
            service = TransactionService(uow)
            updated_tx = service.update_transaction(tx_id, user_id, data)
            response_data = updated_tx.to_dict()

        return jsonify(response_data), 200

    except Exception as e:
        return parse_exception(e)


@bp.route('/<int:tx_id>', methods=['GET'])
@jwt_required()
def get_transaction(tx_id: int):
    user_id = int(get_jwt_identity())
    try:
        with UnitOfWork() as uow:
            service = TransactionService(uow)
            tx = service.get_transaction(tx_id, user_id)
            response_data = tx.to_dict()

        return jsonify(response_data), 200

    except Exception as e:
        return parse_exception(e)
