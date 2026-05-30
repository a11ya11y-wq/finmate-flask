import logging
from datetime import datetime, timedelta, timezone
from .schemas import ReportRequestSchema
from core_service.exceptions import BusinessLogicError, ResourceNotFound
from core_service.uow import UnitOfWork
import json
from core_service import extensions
from core_service.models.report_model import ReportStatus
from core_service.utils.caching import invalidate_cache, redis_cache


logger = logging.getLogger(__name__)



def reports_key_builder(self, user_id):
    return f"reports:{user_id}"

class ReportService:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def generate_pdf_report(self, user_id: int, data: dict) -> tuple[dict, int]:
        self._clear_related_caches(user_id)
        validated_data = ReportRequestSchema.model_validate(data)
        payload = validated_data.model_dump(mode='json', exclude_unset=True)

        if not payload:
            raise BusinessLogicError("No valid fields to generate report.")
        payload['userId'] = user_id

        start_date = validated_data.startDate
        end_date = validated_data.endDate

        user = self.uow.auth.find_user_by_id(user_id)
        if not user:
            logger.warning(f"User entity not found for user_id: {user_id}")
            raise ResourceNotFound("User not found.")
        
        existing_report = self.uow.reports.get_active_report_by_period(user_id, start_date, end_date)
        if existing_report:
            logger.info(f"Existing report found for user_id: {user_id} in the specified period. Returning existing report.")

            if existing_report.status == ReportStatus.PROCESSED:
                if existing_report.expire_at and datetime.now(timezone.utc) > existing_report.expire_at:
                    logger.info(f"Report {existing_report.id} expired. Generating a new one.")
                    self.uow.reports.update_report_status(existing_report.id, ReportStatus.EXPIRED, None)
                    report = self.uow.reports.create_report(user_id, start_date, end_date)
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
                report = self.uow.reports.create_report(user_id, start_date, end_date)

        else:
            report = self.uow.reports.create_report(user_id, start_date, end_date)
        self.uow.flush() 

        transactions = self.uow.transactions.get_tx_by_period(user_id, start_date, end_date)


        if not transactions:
            logger.info(f"No transactions found for user_id: {user_id} in the specified period.")
            self.uow.reports.update_report_status(report.id, ReportStatus.FAILED)
            self.uow.flush()
            raise BusinessLogicError("No transactions found for the specified period for report.")
        self.uow.flush()
        
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
            self.uow.reports.update_report_status(report.id, ReportStatus.FAILED)
            self.uow.flush()
            return {"error": "Failed to start report generation process. Please try again later."}, 400

        return {
            "id": report.id,
            "status": report.status.value,
        }, 202
 

    def get_report_status(self, user_id: int, report_id: int) -> tuple[dict, int]:

        report = self.uow.reports.get_report_by_id(report_id)
        if not report or report.user_id != user_id:
            logger.warning(f"Report with id {report_id} not found for user_id: {user_id}")
            raise ResourceNotFound("Report not found or access denied.")

        if report.status == ReportStatus.PROCESSED:
            if report.expire_at and datetime.now(timezone.utc) > report.expire_at:
                self.uow.reports.update_report_status(report_id, ReportStatus.EXPIRED, None)
                self.uow.flush()
                self._clear_related_caches(user_id)
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
                self.uow.reports.update_report_status(report_id, ReportStatus.FAILED)
                self.uow.flush()
                self._clear_related_caches(user_id)
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
                self.uow.reports.update_report_status(report_id, ReportStatus.FAILED)
                self.uow.flush()
                self._clear_related_caches(user_id)
                return {
                    "id": report_id,
                    "status": ReportStatus.FAILED.value,
                    "error": "Report generation failed due to missing file URL."
                }, 400
            
            expire_time = datetime.now(timezone.utc) + timedelta(days=3)
            self.uow.reports.update_report_status(report_id, ReportStatus.PROCESSED, file_url, expire_time)
            self.uow.flush()
            self._clear_related_caches(user_id)
            extensions.redis_client.delete(redis_result_key)
            return {
                "id": report_id,
                "status": ReportStatus.PROCESSED.value,
                "fileUrl": file_url
            }, 200

        elif status == "error":
            error_msg = result_data.get("message", "An error occurred during report generation.")
            self.uow.reports.update_report_status(report_id, ReportStatus.FAILED)
            self.uow.flush()
            self._clear_related_caches(user_id)
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
    
    @redis_cache(ttl=3600, key_builder=reports_key_builder)
    def get_report_history(self, user_id: int) -> list[dict]:
        reports = self.uow.reports.get_report_history(user_id)
        report_history = []
        
        needs_update = False 

        for report in reports:
            display_status = report.status.value
            display_url = report.file_url

            if report.status == ReportStatus.PROCESSED and report.expire_at and datetime.now(timezone.utc) > report.expire_at:
                report.status = ReportStatus.EXPIRED
                report.file_url = None
                self.uow.reports.update_report_status(report.id, ReportStatus.EXPIRED, None, report.expire_at)
                
                display_status = ReportStatus.EXPIRED.value
                display_url = None
                needs_update = True
                
            report_history.append({
                "id": report.id,
                "status": display_status,
                "startDate": report.start_date.isoformat() if report.start_date else None,
                "endDate": report.end_date.isoformat() if report.end_date else None,
                "createdAt": report.created_at.isoformat() if report.created_at else None,
                "fileUrl": display_url,
                "expireAt": report.expire_at.isoformat() if report.expire_at else None
            })
            
        if needs_update:
            self.uow.flush()
            self._clear_related_caches(user_id)
            
        return report_history
        
    def _clear_related_caches(self, user_id: int):
        self.uow.on_commit(lambda: invalidate_cache(f"reports:{user_id}*"))

