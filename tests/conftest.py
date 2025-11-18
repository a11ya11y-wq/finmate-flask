import pytest

from backend.finmate import create_app, db

#TODO: Добавить тест юзер і переписать ДБ_Сешн

BASE_REGISTER_JSON = {
    "username": "auth_test_user",
    "email": "auth_test@example.com",
    "password": "ValidPassword123",
    "confirm_password": "ValidPassword123"
}


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
        db.drop_all()
        db.create_all()
        yield db.session

@pytest.fixture(scope="function")
def auth_headers(client, db_session):
    client.post("/api/v1/auth/register", json=BASE_REGISTER_JSON)
    login_data = {
        "email": BASE_REGISTER_JSON["email"],
        "password": BASE_REGISTER_JSON["password"]
    }

    response = client.post("/api/v1/auth/login", json=login_data)
    json_data = response.get_json()
    token = json_data.get('access_token')

    return {
        "Authorization": f"Bearer {token}"
    }