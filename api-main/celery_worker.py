from core_service import create_app
from celery.signals import task_prerun, task_postrun
from core_service.extensions import celery
import os

conf_name = os.getenv('FLASK_CONFIG') or 'default'
app = create_app(config_name=conf_name)


_app_ctxs = {}

@task_prerun.connect
def setup_flask_context(task_id, task, **kwargs):
    ctx = app.app_context()
    ctx.push()
    _app_ctxs[task_id] = ctx

@task_postrun.connect
def teardown_flask_context(task_id, task, **kwargs):
    ctx = _app_ctxs.pop(task_id, None)
    if ctx:
        ctx.pop()