import os

import pytest
from core_service import create_app, db


os.environ['FLASK_CONFIG'] = 'testing'

@pytest.fixture(scope='session')
def app():
    app = create_app(config_name='testing')
    with app.app_context():
        yield app


@pytest.fixture(scope='session')
def client(app):
    return app.test_client()