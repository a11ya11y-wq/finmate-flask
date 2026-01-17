from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask import jsonify
import redis
from celery import Celery


db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
celery = Celery()

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({
        "error": "Invalid token",
        "details": error
    }), 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify({
        "error": "Missing token",
        "details": error
    }), 401


redis_client = None

def init_redis(app):
    global redis_client
    redis_url = app.config.get('REDIS_URL')

    redis_client = redis.from_url(redis_url, decode_responses=True)

    return redis_client

def init_celery(app):
    celery.config_from_object(app.config, namespace='CELERY')

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery