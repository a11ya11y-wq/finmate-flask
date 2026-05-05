from celery.utils.log import get_task_logger
from core_service.extensions import celery
from .service import ReportService


logger = get_task_logger(__name__)


@celery.task(
    name="tasks.reports.generate",
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def task_generate_report(self, user_id: int, data: dict):
    logger.info(f"Starting report generation task for user {user_id}")

    try:
        service = ReportService()
        result = service.generate_pdf_report(user_id, data)

        logger.info(f"Report generation task completed successfully for user {user_id}")
        return result

    except Exception as exc:
        logger.error(f"Error in task_generate_report: {exc}")
        raise self.retry(exc=exc)