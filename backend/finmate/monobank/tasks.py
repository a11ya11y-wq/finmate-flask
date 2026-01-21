from celery.utils.log import get_task_logger

from celery import shared_task
from .service import MonobankService


logger = get_task_logger(__name__)

@shared_task
def task_sync_monobank_tx(user_id):
    logger.info(f"Starting Monobank transaction sync task for user {user_id}")

    service = MonobankService()
    added_count = service.sync_tx(user_id)
    return {
        "added_count": added_count,
        "message": f"Successfully synchronized {added_count} transaction(s)"
    }

