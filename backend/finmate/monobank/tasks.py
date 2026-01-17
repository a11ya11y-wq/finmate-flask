from finmate.extensions import celery
from .service import MonobankService

@celery.task
def task_sync_monobank_tx(user_id):
    service = MonobankService()
    service.sync_tx(user_id)
    return f"User {user_id} synced."
