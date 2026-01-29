from flask_jwt_extended import jwt_required, get_jwt_identity
from flask import  jsonify
import logging

from . import bp
from .service import MonobankService
from finmate.utils.error_parser import parse_exception
from .tasks import task_sync_monobank_tx
from finmate.extensions import celery, limiter


logger = logging.getLogger(__name__)

service = MonobankService()


@bp.route('/sync-transactions', methods=["POST"])
@jwt_required()
@limiter.limit("2 per minute")
def sync_transactions():
    try:
        user_id = int(get_jwt_identity())
        logger.info(f"Initiating Monobank transaction sync for user {user_id}")

        task = task_sync_monobank_tx.delay(user_id)

        return jsonify({"task_id": task.id}), 202

    except Exception as e:
        return parse_exception(e)


@bp.route('/tasks/<task_id>', methods=["GET"])
@jwt_required()
def get_task_status(task_id):
    task_result = celery.AsyncResult(task_id)
    response = {
        "task_id": task_id,
        "status": task_result.state, # PENDING, STARTED, SUCCESS, FAILURE
        "result": None
    }

    if task_result.state == 'SUCCESS':
        response["result"] = task_result.result

    elif task_result.state == 'FAILURE':
        response["result"] = str(task_result.info)

    return jsonify(response)