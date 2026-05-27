from celery.utils.log import get_task_logger

from celery import shared_task
from .service import MonobankService
from core_service.uow import UnitOfWork


logger = get_task_logger(__name__)

@shared_task
def task_sync_monobank_tx(user_id):
    logger.info(f"Starting Monobank transaction sync task for user {user_id}")
    
    with UnitOfWork() as uow:
        service = MonobankService(uow)
        added_count = service.sync_tx(user_id)

    if added_count > 0:
        try:
            MonobankService._clear_related_caches(user_id)
        except Exception as e:
                logger.error(f"Post-commit action failed: {e}")

    return {
        "added_count": added_count,
        "message": f"Successfully synchronized {added_count} transaction(s)"
    }

