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

        report_dict, status_code = service.generate_pdf_report(user_id, data)

        return jsonify(report_dict), status_code

    except Exception as e:
        return parse_exception(e)

@bp.route("/generate-pdf/<int:report_id>/status", methods=['GET'])
@jwt_required()
def get_report_status(report_id):
    try:
        user_id = int(get_jwt_identity())
        response_data, status_code = service.get_report_status(user_id, report_id)
        return jsonify(response_data), status_code

    except Exception as e:
        return parse_exception(e)

@bp.route("/history", methods=['GET'])
@jwt_required()
def get_report_history():
    try:
        user_id = int(get_jwt_identity())
        response_data = service.get_report_history(user_id)
        return jsonify(response_data), 200

    except Exception as e:
        return parse_exception(e)
    
    