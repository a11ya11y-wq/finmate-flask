import os

import allure
import pytest
import redis
from core_service import create_app, db, extensions
from core_service.models.category_model import Category
from core_service.models.user_model import Users
from flask_jwt_extended import create_access_token
from sqlalchemy.orm import scoped_session, sessionmaker


@pytest.fixture(scope="session")
@allure.title("Prepare DB for tests")
def init_database(app):
    with app.app_context():
        with allure.step("Drop and create all tables"):
            db.drop_all()
            db.create_all()
        yield db


@pytest.fixture(scope="function")
@allure.title("Izolate DB session for test (Transaction)")
def db_session(app, init_database):
    with app.app_context():
        with allure.step("Connect to the database and start a transaction"):
            connection = db.engine.connect()
            transaction = connection.begin()

            session_factory = sessionmaker(bind=connection)
            session = scoped_session(session_factory)

            original_session = db.session
            db.session = session

        yield session

        with allure.step("Rollback the transaction and close the connection"):
            db.session = original_session
            transaction.rollback()
            connection.close()
            session.remove()


@pytest.fixture(scope="function")
@allure.title("Create test user and return auth headers")
def auth_headers(db_session):

    with allure.step("Create test user and categories"):
        user = Users(
            id=1,
            username="test",
            email="test@test.com",
            password_hash="ValidPassword123",
        )
        db_session.add(user)
        db_session.flush()

        for i in range(1, 7):
            cat = Category(id=i, name=f"Test Category{i}", user_id=user.id)
            db_session.add(cat)

    with allure.step("Commit the user and categories to the database"):
        db_session.commit()

    with allure.step("Create access token"):
        access_token = create_access_token(identity=str(user.id))

    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture(scope="function", autouse=True)
@allure.title("Izolated Redis client for test")
def test_redis(app):

    with allure.step("Create a new Redis client for testing"):
        redis_host = os.environ.get("REDIS_HOST", "localhost")
        client = redis.Redis(host=redis_host, port=6379, db=1, decode_responses=True)
        client.flushdb()

    with allure.step("Replace the original Redis client with the test client"):
        original_redis = extensions.redis_client
        extensions.redis_client = client

    yield client

    with allure.step(
        "Flush the test Redis database and restore the original Redis client"
    ):
        client.flushdb()
        client.close()
        extensions.redis_client = original_redis
