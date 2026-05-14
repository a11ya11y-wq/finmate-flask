from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import redis
from celery import Celery
import logging

logger = logging.getLogger(__name__)

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
celery = Celery()
redis_client = None

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["2000 per day", "500 per hour"]
)

    
def init_limiter(app):
    if app.config.get("TESTING"):
        app.config["RATELIMIT_STORAGE_URI"] = "memory://"
        limiter.enabled = False
    else:
        app.config["RATELIMIT_STORAGE_URI"] = app.config["REDIS_URL"]

    limiter.init_app(app)

def init_redis(app):
    global redis_client

    redis_url = app.config.get('REDIS_URL')
    if not redis_url:
        logger.warning("Redis disabled (no REDIS_URL)")
        redis_client = None
        return None
    try:
        redis_client = redis.Redis.from_url(redis_url, decode_responses=True)
        response = redis_client.ping()
        logger.info(f"Redis connection successful: {response}")
        return redis_client

    except redis.ConnectionError as e:
        logger.error(f"Redis connection error: {e}")
        redis_client = None
        return None


def init_celery(app):
    if app.config.get("TESTING"):
        return None
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