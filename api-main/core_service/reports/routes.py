from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from core_service.reports import bp
from core_service.utils.error_parser import parse_exception
from core_service.reports.service import ReportService
from core_service.extensions import limiter, celery
from .tasks import task_generate_report
import logging


logger = logging.getLogger(__name__)

service = ReportService()

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

@bp.route("/status/<task_id>", methods=['GET'])
@jwt_required()
def get_task_status(task_id):
    try:
        task_result = celery.AsyncResult(task_id)

        res = task_result.result

        if res is None:
            return jsonify({"status": task_result.state, "msg": "Waiting for worker..."}), 200

        if task_result.state == 'PENDING':
            return jsonify({
                "status": "PENDING",
                "msg": res.get('msg', 'Report generation is pending')
            }), 200

        elif task_result.state == 'SUCCESS':
                return jsonify({
                    "status": "SUCCESS",
                    "data": res.get('fileName'),
                    "msg": res.get('msg', 'Report generated successfully')
                }), 200

        elif task_result.state == 'FAILURE':
            return jsonify({
                "status": "FAILED",
                "error": str(task_result.info),
                "msg": res.get('msg', 'Report generation failed')
            }), 500

        return jsonify({"status": task_result.state}), 200

    except Exception as e:
        return parse_exception(e)


@bp.route("/download/<file_name>", methods=['GET'])
@jwt_required()
def download_report(file_name): #TODO: add assert report.id == current_user_id
    try:
        report_file = service.download_report(file_name)
        return report_file
    except Exception as e:
        return parse_exception(e)