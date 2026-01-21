import pytest
from sqlalchemy.orm import scoped_session, sessionmaker
from flask_jwt_extended import create_access_token
from finmate.models.user_model import Users
from finmate.models.category_model import Category

from finmate import create_app, db



@pytest.fixture(autouse=True)
def mock_redis(mocker):
    mock = mocker.patch("finmate.extensions.redis_client")

    mock.get.return_value = None # blacklist (logout)
    mock.set.return_value = True # caching (data)
    return mock


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


@pytest.fixture(scope='function')
def db_session(app):
    with app.app_context():
        connection = db.engine.connect()
        transaction = connection.begin()

        session_factory = sessionmaker(bind=connection)
        session = scoped_session(session_factory)

        original_session = db.session
        db.session = session

        yield session

        db.session = original_session
        transaction.rollback()
        connection.close()
        session.remove()


@pytest.fixture(scope="function")
def auth_headers(db_session):
    user = Users(
        id=1,
        username="test",
        email="test@test.com",
        password_hash="ValidPassword123"
    )
    for i in range(1, 7):
        cat = Category(
            id=i,
            name=f"Test Category{i}",
            user_id=1
        )
        db_session.add(cat)
    db_session.add(user)
    db_session.commit()

    access_token = create_access_token(identity=str(user.id))

    return {"Authorization": f"Bearer {access_token}"}