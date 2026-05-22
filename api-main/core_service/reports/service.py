from datetime import datetime
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
from core_service.models.report_model import ReportStatus, Reports



logger = logging.getLogger(__name__)



class ReportService:

    def __init__(self):
        self.upload_folder = "/app/uploads"

    def generate_pdf_report(self, user_id: int, data: dict) -> tuple[dict, int]:
        validated_data = ReportRequestSchema.model_validate(data)
        payload = validated_data.model_dump(mode='json', exclude_unset=True)

        if not payload:
            raise BusinessLogicError("No valid fields to generate report.")
        payload['userId'] = user_id

        start_date = validated_data.startDate
        end_date = validated_data.endDate

        with UnitOfWork() as uow:
            user = uow.auth.find_user_by_id(user_id)
            if not user:
                logger.warning(f"User entity not found for user_id: {user_id}")
                raise ResourceNotFound("User not found.")
            
            existing_report = uow.reports.get_active_report_by_period(user_id, start_date, end_date)
            if existing_report:
                logger.info(f"Existing report found for user_id: {user_id} in the specified period. Returning existing report.")

                if existing_report.status == ReportStatus.PROCESSED:
                    return existing_report.to_dict(), 200
                elif existing_report.status == ReportStatus.PENDING:
                    raise BusinessLogicError("Report generation is already in progress for the specified period.")
                elif existing_report.status in [ReportStatus.FAILED, ReportStatus.EXPIRED]:
                    report = uow.reports.create_report(user_id, start_date, end_date)

            else:
                report = uow.reports.create_report(user_id, start_date, end_date)
            uow.flush() # Ensure report.id is generated before fetching transactions

            transactions = uow.transactions.get_tx_by_period(user_id, start_date, end_date)


            if not transactions:
                logger.info(f"No transactions found for user_id: {user_id} in the specified period.")
                uow.reports.update_report_status(report.id, ReportStatus.FAILED)
                uow.commit()
                raise BusinessLogicError("No transactions found for the specified period for report.")
            uow.commit()

        task_payload = {
            "reportId": report.id,
            "user": {
                "username": user.username,
                "email": user.email
            },
            "transactions": transactions
        }

        try:
            extensions.redis_client.rpush("pdf_task_queue", json.dumps(task_payload))
            logger.info(f"Report generation task enqueued for user_id: {user_id} with report_id: {report.id}")
        except Exception as e:
            logger.error(f"Failed to enqueue report generation task for user_id: {user_id} with report_id: {report.id}. Error: {str(e)}")
            with UnitOfWork() as uow:
                uow.reports.update_report_status(report.id, ReportStatus.FAILED)
                uow.commit()
            raise BusinessLogicError("Failed to start report generation process. Please try again later.")

        return report.to_dict(), 202
 

    def get_report_status(self, user_id: int, report_id: int) -> tuple[dict, int]:
         with UnitOfWork() as uow:

            report = uow.reports.get_report_by_id(report_id)
            if not report or report.user_id != user_id:
                logger.warning(f"Report with id {report_id} not found for user_id: {user_id}")
                raise ResourceNotFound("Report not found or access denied.")

            if report.status == ReportStatus.PROCESSED:
                return {
                    "status": report.status.value,
                    "fileName": report.file_name
                }, 200
            elif report.status in [ReportStatus.FAILED, ReportStatus.EXPIRED]:
                return {
                    "status": report.status.value,
                    "error": "Report generation failed."
                }, 400

            redis_result_key = f"report_result:{report_id}"
            result = extensions.redis_client.get(redis_result_key)

            if not result:
                return { "status": "pending" }, 202

            result_data = json.loads(result)
            status = result_data.get("status")
    
            if status == "success":
                file_name = result_data.get("fileName")
                uow.reports.update_report_status(report_id, ReportStatus.PROCESSED, file_name)
                uow.commit()
                extensions.redis_client.delete(redis_result_key)
                return {
                    "status": status,
                    "fileName": file_name
                }, 200

            elif status == "error":
                error_msg = result_data.get("message", "An error occurred during report generation.")
                uow.reports.update_report_status(report_id, ReportStatus.FAILED)
                uow.commit()
                extensions.redis_client.delete(redis_result_key)
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

