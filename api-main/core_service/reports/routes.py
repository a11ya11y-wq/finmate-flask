from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from core_service.reports import bp
from core_service.utils.error_parser import parse_exception
from core_service.reports.service import ReportService
from core_service.extensions import limiter, celery
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

        request_id= service.generate_pdf_report(user_id, data)

        return jsonify({
            "message": "Report generation started. You will receive the report shortly.",
            "status": "PENDING",
            "request_id": request_id
        }), 202

    except Exception as e:
        return parse_exception(e)

@bp.route("/generate-pdf/<request_id>/status", methods=['GET'])
@jwt_required()
def get_report_status(request_id):
    try:
        response_data, status_code = service.get_report_status(request_id)
        return jsonify(response_data), status_code

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