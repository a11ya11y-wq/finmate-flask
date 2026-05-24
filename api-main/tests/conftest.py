import pytest
from core_service import create_app, db


@pytest.fixture(scope='session')
def app():
    app = create_app(config_name='testing')
    with app.app_context():
        db.drop_all()
        db.create_all()
        yield app


@pytest.fixture(scope='session')
def client(app):
    return app.test_client()