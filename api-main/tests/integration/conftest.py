import pytest
from sqlalchemy.orm import scoped_session, sessionmaker
from flask_jwt_extended import create_access_token
from core_service.models.user_model import Users
from core_service.models.category_model import Category

from core_service import create_app, db


@pytest.fixture(scope='session')
def init_database(app):
    with app.app_context():
        db.drop_all()
        db.create_all()
        yield db

        db.drop_all()

@pytest.fixture(scope='function')
def db_session(app, init_database):
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