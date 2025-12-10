from flask_jwt_extended import jwt_required, get_jwt_identity
from flask import  jsonify

from . import bp
from .service import MonobankService
from backend.finmate.utils.error_parser import parse_exception


service = MonobankService()


@bp.route('/sync-transactions', methods=["POST"])
@jwt_required()
def sync_transactions(): #TODO: Захист від спаму (в бд добавить ласт_моно_реквест(Дейттайм))
    try:
        user_id = int(get_jwt_identity())
        added_count = service.sync_tx(user_id)

        if added_count == 0:
            message = "Your transactions are already up to date."
        else:
            message = f"Successfully added {added_count} new transactions!"

        return jsonify({"message": message, "count": added_count}), 200

    except Exception as e:
        return parse_exception(e)