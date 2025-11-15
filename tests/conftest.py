import pytest

from backend.finmate import create_app, db


@pytest.fixture(scope='session')
def app():
    app = create_app(config_name='testing')
    with app.app_context():
        db.drop_all()
        db.create_all()
        yield app


@pytest.fixture(scope='module')
def client(app):
    return app.test_client()


@pytest.fixture(scope='function')
def db_session(app):
    with app.app_context():

        yield db.session

        db.session.rollback()