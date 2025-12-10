import pytest


BASE_REGISTER_JSON = {
    "username": "testuser",
    "email": "test@example.com",
    "password": "ValidPassword123",
    "confirm_password": "ValidPassword123"
}

# def test_register_sad_path
register_sad_paths = [
        # Diferent passwords (Pydantic)
        (
            BASE_REGISTER_JSON | {"email": "test1@example.com", "confirm_password": "DIFFERENT"},
            422,
            "Passwords do not match"
        ),

        # Short password (Pydantic)
        (
            BASE_REGISTER_JSON | {"email": "test2@example.com", "password": "123", "confirm_password": "123"},
            422,
            "at least 6 characters"
        ),

        # Invalid email (Pydantic)
        (
            BASE_REGISTER_JSON | {"email": "not-an-email"},
            422,
            "value is not a valid email address"
        ),

        # wo username (Pydantic)
        (
            {"password": "123", "email": "a@b.c", "confirm_password": "123"},
            422,
            "Field required"
        ),
        # Short username (Pydantic)
        (
            BASE_REGISTER_JSON | {"username": "us"},
            422,
            "at least 4 characters"

        )
    ]

# def test_register_existing_user
registered_users = [
        # User exist by email (Service)
        (
            BASE_REGISTER_JSON | {"username": "ANOTHER US"},
            409,
            "Email already registered."
        ),
        # User exist by username (Service)
        (
            BASE_REGISTER_JSON  | {"email": "another@email.com"},
            409,
            "Username already registered"
        )
    ]

@pytest.mark.usefixtures("db_session")
class TestRegister:

    def test_register_success(self, client):
        response = client.post("/api/v1/auth/register", json=BASE_REGISTER_JSON)

        assert response.status_code == 201


    @pytest.mark.parametrize(
        "test_data, expected_status, expected_error_fragment",
        register_sad_paths
    )
    def test_register_fails(self, client, test_data, expected_status, expected_error_fragment):
        response = client.post("/api/v1/auth/register", json=test_data)
        assert response.status_code == expected_status

        json_data = response.get_json()
        assert expected_error_fragment in str(json_data)


    @pytest.mark.parametrize(
        "test_data, expected_status, expected_error_fragment",
        registered_users
    )
    def test_register_existing_user(self, client, test_data, expected_status, expected_error_fragment):
        client.post("/api/v1/auth/register", json=BASE_REGISTER_JSON)

        response = client.post("/api/v1/auth/register", json=test_data)
        assert response.status_code == expected_status

        json_data = response.get_json()
        assert expected_error_fragment in str(json_data)


@pytest.mark.usefixtures("db_session")
class TestLogin:

    def test_login_success(self, client):
        client.post("/api/v1/auth/register", json=BASE_REGISTER_JSON)
        login_data = {
            "email": BASE_REGISTER_JSON["email"],
            "password": BASE_REGISTER_JSON["password"]
        }

        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 200
        json_data = response.get_json()
        assert "access_token" in json_data


    def test_login_no_user(self, client):
        login_data = {
            "email": "non_existing@example.com",
            "password": "password123"
        }
        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 401


    def test_login_wrong_password(self, client):
        client.post("/api/v1/auth/register", json=BASE_REGISTER_JSON)

        login_data = {
            "email": BASE_REGISTER_JSON["email"],
            "password": "WRONG_PASSWORD_!@#"
        }
        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 401
        assert "Invalid email or password" in str(response.get_json())


#TODO: Add and test logout
