from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask import jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import redis
from celery import Celery


db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
celery = Celery()

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["2000 per day", "500 per hour"],
    storage_uri="redis://redis:6379/0"
)


redis_client = None

def init_redis(app):
    global redis_client
    redis_url = app.config.get('REDIS_URL')

    redis_client = redis.from_url(redis_url, decode_responses=True)

    return redis_client

def init_celery(app):
    celery.conf.update(app.config)

    celery.conf.update(
        broker_url=app.config.get("CELERY_BROKER_URL"),
        result_backend=app.config.get("CELERY_RESULT_BACKEND"),
    )

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery