from finmate.extensions import celery
from .service import MonobankService

@celery.task
def task_sync_monobank_tx(user_id):
    service = MonobankService()
    added_count = service.sync_tx(user_id)
    return {
        "added_count": added_count,
        "message": f"Successfully synchronized {added_count} transaction(s)"
    }

