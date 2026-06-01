import os

import pytest
from core_service import create_app, db


os.environ['FLASK_CONFIG'] = 'testing'

@pytest.fixture(scope='session')
def app():
    app = create_app(config_name='testing')
    app.config['REDIS_URL'] = os.environ.get('REDIS_URL', 'redis://localhost:6379/1')
    with app.app_context():
        yield app


@pytest.fixture(scope='session')
def client(app):
    return app.test_client()