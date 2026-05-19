import logging
import time

from .schemas import ReportRequestSchema
from core_service.exceptions import BusinessLogicError, ResourceNotFound
from core_service.uow import UnitOfWork
import uuid
import json
from core_service import extensions
import os
from flask import jsonify, send_from_directory



logger = logging.getLogger(__name__)



class ReportService:

    def __init__(self):
        self.upload_folder = "/app/uploads"

    def generate_pdf_report(self, user_id: int, data: dict):
        validated_data = ReportRequestSchema.model_validate(data)
        payload = validated_data.model_dump(mode='json', exclude_unset=True)

        if not payload:
            raise BusinessLogicError("No valid fields to generate report.")
        payload['userId'] = user_id

        with UnitOfWork() as uow:
            user = uow.auth.find_user_by_id(user_id)
        if not user:
            logger.warning(f"User entity not found for user_id: {user_id}")
            raise ResourceNotFound("User not found.")

        request_id = str(uuid.uuid4())
        payload['requestId'] = request_id

        message = {
            "pattern": 'reports_queue',
            "data": payload,
        }
        logger.info(f"Payload for report generation: {payload}=======")

        try:
            status_key = f"request:{request_id}:status"
            extensions.redis_client.setex(status_key, 3600, "PENDING") # Value is set to "PENDING"

            extensions.redis_client.publish('reports_queue', json.dumps(message))
            logger.info(f"Published report job {request_id} to reports_queue.")

            return request_id

        except Exception as e:
            logger.error(f"Failed to publish report generation job: {str(e)}")
            raise BusinessLogicError(f"Failed to initiate report generation, please try again later.")


    def get_report_status(self, request_id: str) -> tuple[dict, int]:
        status_key = f"request:{request_id}:status"
        file_key = f"request:{request_id}:file"

        status = extensions.redis_client.get(status_key)
        status = status.upper() if status else None

        if not status:
            return jsonify({"error": "Request ID not found or expired"}), 404

        if status == "PROCESSED":
            file_resp = extensions.redis_client.get(file_key)
            file_name = file_resp if file_resp else None
            return {
                "status": status,
                "fileName": file_name
            }, 200

        elif status == "FAILED":
            error_resp = extensions.redis_client.get(f"request:{request_id}:error")
            error_msg = error_resp if error_resp else "Unknown error during generation"
            return {
                "status": status,
                "error": error_msg
            }, 400

        else:
            return {
                "status": status
            }, 202


    def download_report(self, file_name: str):
        file_path = os.path.join(self.upload_folder, file_name)

        if not os.path.exists(file_path):
            raise BusinessLogicError("Report file not found on server.")

        return send_from_directory(
            self.upload_folder,
            file_name,
            as_attachment=True
        )

