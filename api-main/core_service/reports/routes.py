from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from core_service.reports import bp
from core_service.utils.error_parser import parse_exception
from core_service.extensions import limiter
from .tasks import task_generate_report
import logging


logger = logging.getLogger(__name__)

@bp.route("/generate-pdf", methods=['POST'])
@jwt_required()
@limiter.limit("2 per minute")
def generate_pdf_report():
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json() # startDate and endDate
        logger.info(f"Received request to generate PDF report for user {user_id}")

        task = task_generate_report.delay(user_id, data)

        return jsonify({
            "message": "Report generation started. You will receive the report shortly.",
            "taskId": task.id
        }), 202

    except Exception as e:
        return parse_exception(e)