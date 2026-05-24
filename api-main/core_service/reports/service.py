import logging
from datetime import datetime, timedelta, timezone
from .schemas import ReportRequestSchema
from core_service.exceptions import BusinessLogicError, ResourceNotFound
from core_service.uow import UnitOfWork
import json
from core_service import extensions
from core_service.models.report_model import ReportStatus



logger = logging.getLogger(__name__)



class ReportService:

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
                    if existing_report.expire_at and datetime.now(timezone.utc) > existing_report.expire_at:
                        logger.info(f"Report {existing_report.id} expired. Generating a new one.")
                        uow.reports.update_report_status(existing_report.id, ReportStatus.EXPIRED)
                        report = uow.reports.create_report(user_id, start_date, end_date)
                    else:
                        return {
                            "id": existing_report.id,
                            "status": existing_report.status.value,
                            "fileUrl": existing_report.file_url
                        }, 200
                    
                elif existing_report.status == ReportStatus.PENDING:
                    raise BusinessLogicError("Report generation is already in progress for the specified period.")
                
                elif existing_report.status in [ReportStatus.FAILED, ReportStatus.EXPIRED]:
                    logger.info(f"Previous report generation failed or expired for user_id: {user_id}. Generating a new report.")
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

        return {
            "id": report.id,
            "status": report.status.value,
        }, 202
 

    def get_report_status(self, user_id: int, report_id: int) -> tuple[dict, int]:
         with UnitOfWork() as uow:

            report = uow.reports.get_report_by_id(report_id)
            if not report or report.user_id != user_id:
                logger.warning(f"Report with id {report_id} not found for user_id: {user_id}")
                raise ResourceNotFound("Report not found or access denied.")

            if report.status == ReportStatus.PROCESSED:
                if report.expire_at and datetime.now(timezone.utc) > report.expire_at:
                    uow.reports.update_report_status(report_id, ReportStatus.EXPIRED)
                    uow.commit()
                    return {
                        "id": report_id,
                        "status": ReportStatus.EXPIRED.value,
                        "error": "The report link has expired. Please generate a new report."
                    }, 410

                return {
                    "id": report_id,
                    "status": report.status.value,
                    "fileUrl": report.file_url
                }, 200
            
            elif report.status in [ReportStatus.FAILED, ReportStatus.EXPIRED]:
                return {
                    "id": report_id,
                    "status": report.status.value,
                    "error": "Report generation failed."
                }, 400
            
            elif report.status == ReportStatus.PENDING:
                timeout_limit = report.created_at + timedelta(hours=1)
                
                if datetime.now(timezone.utc) > timeout_limit:
                    logger.error(f"Report {report_id} stuck in PENDING for too long. Marking as FAILED.")
                    uow.reports.update_report_status(report_id, ReportStatus.FAILED)
                    uow.commit()
                    return {
                        "id": report_id,
                        "status": ReportStatus.FAILED.value,
                        "error": "The report generation timed out. Please request a new report."
                    }, 400

            redis_result_key = f"report_result:{report_id}"
            result = extensions.redis_client.get(redis_result_key)

            if not result:
                return { "id": report_id, "status": ReportStatus.PENDING.value }, 202

            result_data = json.loads(result)
            status = result_data.get("status")
    
            if status == "success":
                file_url = result_data.get("fileUrl")

                if not file_url:
                    logger.error(f"Report {report_id} marked as success but no fileUrl provided in Redis result.")
                    uow.reports.update_report_status(report_id, ReportStatus.FAILED)
                    uow.commit()
                    return {
                        "id": report_id,
                        "status": ReportStatus.FAILED.value,
                        "error": "Report generation failed due to missing file URL."
                    }, 400
                
                expire_time = datetime.now(timezone.utc) + timedelta(days=3)
                uow.reports.update_report_status(report_id, ReportStatus.PROCESSED, file_url, expire_time)
                uow.commit()
                extensions.redis_client.delete(redis_result_key)
                return {
                    "id": report_id,
                    "status": ReportStatus.PROCESSED.value,
                    "fileUrl": file_url
                }, 200

            elif status == "error":
                error_msg = result_data.get("message", "An error occurred during report generation.")
                uow.reports.update_report_status(report_id, ReportStatus.FAILED)
                uow.commit()
                extensions.redis_client.delete(redis_result_key)
                return {
                    "id": report_id,
                    "status": ReportStatus.FAILED.value,
                    "error": error_msg
                }, 400

            else:
                return {
                    "id": report_id,
                    "status": status
                }, 202
