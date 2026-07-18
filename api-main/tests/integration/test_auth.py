import allure
import pytest

BASE_REGISTER_JSON = {
    "username": "testuser",
    "email": "test@example.com",
    "password": "ValidPassword123",
    "confirm_password": "ValidPassword123",
}

# def test_register_sad_path
register_sad_paths = [
    # Diferent passwords (Pydantic)
    (
        BASE_REGISTER_JSON
        | {"email": "test1@example.com", "confirm_password": "DIFFERENT"},
        422,
        "Passwords do not match",
    ),
    # Short password (Pydantic)
    (
        BASE_REGISTER_JSON
        | {"email": "test2@example.com", "password": "123", "confirm_password": "123"},
        422,
        "at least 6 characters",
    ),
    # Invalid email (Pydantic)
    (
        BASE_REGISTER_JSON | {"email": "not-an-email"},
        422,
        "value is not a valid email address",
    ),
    # wo username (Pydantic)
    (
        {"password": "123", "email": "a@b.c", "confirm_password": "123"},
        422,
        "Field required",
    ),
    # Short username (Pydantic)
    (BASE_REGISTER_JSON | {"username": "us"}, 422, "at least 4 characters"),
]

# def test_register_existing_user
registered_users = [
    # User exist by email (Service)
    (BASE_REGISTER_JSON | {"username": "ANOTHER US"}, 409, "Email already registered."),
    # User exist by username (Service)
    (
        BASE_REGISTER_JSON | {"email": "another@email.com"},
        409,
        "Username already registered",
    ),
]


@allure.feature("User Management")
@allure.story("Registration")
class TestRegister:

    @allure.title("Successfully register a new user via API")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_register_success(self, client):
        with allure.step("Act: Send POST request to /api/v1/auth/register"):
            response = client.post("/api/v1/auth/register", json=BASE_REGISTER_JSON)

        with allure.step("Assert: Verify 201 Created"):
            assert response.status_code == 201

    @allure.title("API Validation errors on registration")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize(
        "test_data, expected_status, expected_error_fragment", register_sad_paths
    )
    def test_register_fails(
        self, client, test_data, expected_status, expected_error_fragment
    ):
        with allure.step("Act: Send POST with invalid payload"):
            response = client.post("/api/v1/auth/register", json=test_data)

        with allure.step(f"Assert: Verify status {expected_status} and error fragment"):
            assert response.status_code == expected_status
            json_data = response.get_json()
            assert expected_error_fragment in str(json_data)

    @allure.title("Fail registration if user already exists (Conflict)")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize(
        "test_data, expected_status, expected_error_fragment", registered_users
    )
    def test_register_existing_user(
        self, client, test_data, expected_status, expected_error_fragment
    ):
        with allure.step("Arrange: Register initial user"):
            client.post("/api/v1/auth/register", json=BASE_REGISTER_JSON)

        with allure.step("Act: Send POST with duplicated unique fields"):
            response = client.post("/api/v1/auth/register", json=test_data)

        with allure.step(f"Assert: Verify status {expected_status} and conflict error"):
            assert response.status_code == expected_status
            json_data = response.get_json()
            assert expected_error_fragment in str(json_data)


@allure.feature("Authentication")
@allure.story("Login User")
class TestLogin:

    @allure.title("Successfully login user and receive JWT token")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_login_success(self, client):
        with allure.step("Arrange: Register user and prepare valid login payload"):
            client.post("/api/v1/auth/register", json=BASE_REGISTER_JSON)
            login_data = {
                "email": BASE_REGISTER_JSON["email"],
                "password": BASE_REGISTER_JSON["password"],
            }

        with allure.step("Act: Send POST to /api/v1/auth/login"):
            response = client.post("/api/v1/auth/login", json=login_data)

        with allure.step("Assert: Verify 200 OK and presence of access_token"):
            assert response.status_code == 200
            json_data = response.get_json()
            assert "access_token" in json_data

        with allure.step("Assert: Verify refresh token is set in HttpOnly cookie"):
            cookies = response.headers.getlist("Set-Cookie")

            refresh_cookie = next(
                (c for c in cookies if "finmate_refresh_token" in c), None
            )

            assert refresh_cookie is not None, "Refresh token cookie is missing"
            assert "HttpOnly" in refresh_cookie, "Cookie is missing HttpOnly flag!"
            assert (
                "Path=/api/v1/auth/refresh" in refresh_cookie
            ), "Cookie path is incorrect"

    @allure.title("Fail login for non-existent user")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_login_no_user(self, client):
        with allure.step("Arrange: Prepare credentials for non-existent user"):
            login_data = {
                "email": "non_existing@example.com",
                "password": "password123",
            }

        with allure.step("Act: Send POST to /api/v1/auth/login"):
            response = client.post("/api/v1/auth/login", json=login_data)

        with allure.step("Assert: Verify 401 Unauthorized"):
            assert response.status_code == 401

    @allure.title("Fail login with incorrect password")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_login_wrong_password(self, client):
        with allure.step("Arrange: Register user and prepare invalid password payload"):
            client.post("/api/v1/auth/register", json=BASE_REGISTER_JSON)

            login_data = {
                "email": BASE_REGISTER_JSON["email"],
                "password": "WRONG_PASSWORD_!@#",
            }

        with allure.step("Act: Send POST to /api/v1/auth/login"):
            response = client.post("/api/v1/auth/login", json=login_data)

        with allure.step("Assert: Verify 401 Unauthorized and error message"):
            assert response.status_code == 401
            assert "Invalid email or password" in str(response.get_json())


BASE_TRANSACTION_JSON = {
    "amount": 100.0,
    "title": "TEST_TITLE",
    "transaction_type": "expense",
    "category_id": 1,
}


@allure.feature("Authentication")
@allure.story("Logout User")
class TestLogout:

    @allure.title("Successfully logout user and invalidate JWT token")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_logout_success(self, client, auth_headers):
        with allure.step("Act: Send POST to /api/v1/auth/logout"):
            logout_response = client.post("/api/v1/auth/logout", headers=auth_headers)

        with allure.step("Assert: Verify 200 OK and success message"):
            assert logout_response.status_code == 200
            assert "Successfully logged out" in str(logout_response.get_json())

        with allure.step("Assert: Verify refresh token cookie is cleared"):
            cookies = logout_response.headers.getlist("Set-Cookie")
            refresh_cookie = next(
                (c for c in cookies if "finmate_refresh_token" in c), None
            )
            assert refresh_cookie is not None, "Clear cookie instruction is missing"

            assert (
                "finmate_refresh_token=;" in refresh_cookie
                or 'finmate_refresh_token=""' in refresh_cookie
            )

        with allure.step("Act: Attempt to access protected endpoint"):
            tx_response = client.post(
                "/api/v1/transactions/",
                json=BASE_TRANSACTION_JSON,
                headers=auth_headers,
            )

        with allure.step("Assert: Verify 401 Unauthorized for subsequent requests"):
            assert tx_response.status_code == 401
            assert "The token has been revoked" in str(tx_response.get_json())


@allure.title("Successfully refresh access token using valid refresh token")
@allure.feature("Authentication")
@allure.story("Refresh Token")
class TestRefreshAccessToken:

    @allure.title("Successfully refresh access token")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_refresh_success(self, client):
        with allure.step("Arrange: Register and login to set refresh cookie"):
            client.post("/api/v1/auth/register", json=BASE_REGISTER_JSON)
            login_data = {
                "email": BASE_REGISTER_JSON["email"],
                "password": BASE_REGISTER_JSON["password"],
            }

            client.post("/api/v1/auth/login", json=login_data)

        with allure.step("Act: Send POST to /api/v1/auth/refresh"):
            response = client.post("/api/v1/auth/refresh")

        with allure.step("Assert: Verify 200 OK and new access_token"):
            assert response.status_code == 200
            json_data = response.get_json()
            assert "access_token" in json_data

    @allure.title("Fail refresh without refresh cookie")
    @allure.severity(allure.severity_level.NORMAL)
    def test_refresh_no_cookie(self, client):
        with allure.step("Act: Send POST to /refresh with clean client"):
            response = client.post("/api/v1/auth/refresh")

        with allure.step("Assert: Verify 401 Unauthorized"):
            assert response.status_code == 401
            assert "Session expired, please login again" in str(response.get_json())

    @allure.title("Fail refresh with revoked/logged out token")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_refresh_after_logout(self, client):
        with allure.step("Arrange: Login, save cookie, and logout"):
            client.post("/api/v1/auth/register", json=BASE_REGISTER_JSON)
            login_data = {
                "email": BASE_REGISTER_JSON["email"],
                "password": BASE_REGISTER_JSON["password"],
            }
            login_resp = client.post("/api/v1/auth/login", json=login_data)

            cookies = login_resp.headers.getlist("Set-Cookie")
            raw_cookie = next((c for c in cookies if "finmate_refresh_token" in c), "")
            old_token_value = raw_cookie.split("finmate_refresh_token=")[1].split(";")[
                0
            ]
            access_token = login_resp.get_json()["access_token"]
            client.post(
                "/api/v1/auth/logout",
                headers={"Authorization": f"Bearer {access_token}"},
            )

        with allure.step("Act: Forcefully inject old refresh cookie and send request"):
            response = client.post(
                "/api/v1/auth/refresh",
                headers={"Cookie": f"finmate_refresh_token={old_token_value}"},
            )

        with allure.step("Assert: Verify 401 Unauthorized for revoked session"):
            assert response.status_code == 401
            assert "Missing refresh token, please login again" in str(
                response.get_json()
            )
