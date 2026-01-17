from flask_jwt_extended import jwt_required, get_jwt_identity
from flask import  jsonify

from . import bp
from .service import MonobankService
from finmate.utils.error_parser import parse_exception
from .tasks import task_sync_monobank_tx


service = MonobankService()


@bp.route('/sync-transactions', methods=["POST"])
@jwt_required()
def sync_transactions():
    try:
        user_id = int(get_jwt_identity())
        task = task_sync_monobank_tx.delay(user_id)

        return jsonify({"task_id": task.id}), 202

    except Exception as e:
        return parse_exception(e)