import os


class Config:
    SECRET_KEY=os.environ.get('SECRET_KEY')
    ENCRYPTION_KEY=os.environ.get('ENCRYPTION_KEY')
    JWT_SECRET_KEY=os.environ.get('JWT_SECRET_KEY')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL')
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND')


class DevelopmentConfig(Config):
    SQLALCHEMY_DATABASE_URI=os.environ.get('API_MAIN_DATABASE_URL')
    DEBUG = True
    REDIS_URL = os.environ.get('REDIS_URL')

class TestingConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL')
    REDIS_URL = os.environ.get('REDIS_URL')
    TESTING = True
    DEBUG = True

class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI=os.environ.get('API_MAIN_DATABASE_URL')
    DEBUG = False
    REDIS_URL = os.environ.get('REDIS_URL')

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig,
    'production': ProductionConfig
}