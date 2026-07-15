import allure
import pytest
from core_service.models import Users
from tests.integration.conftest import db_session
from werkzeug.security import generate_password_hash


@allure.feature("Profile Management")
@allure.story("Retrieve Profile")
@pytest.mark.usefixtures("db_session")
class TestGetUser:

    @allure.title("Successfully retrieve current user profile")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_get_user_profile_success(self, client, auth_headers):
        with allure.step("Act: Send GET request to /api/v1/profile/me"):
            response = client.get("/api/v1/profile/me", headers=auth_headers)

        with allure.step("Assert: Verify 200 OK"):
            assert response.status_code == 200

    @allure.title("Fail to retrieve profile without authorization")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_user_profile_wo_auth(self, client):
        with allure.step("Act: Send GET request without auth headers"):
            response = client.get("/api/v1/profile/me")

        with allure.step("Assert: Verify 401 Unauthorized"):
            assert response.status_code == 401


@allure.feature("Profile Management")
@allure.story("Update Profile")
@pytest.mark.usefixtures("db_session")
class TestUpdateUser:

    @allure.title("Successfully update user profile data")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_update_user_success(self, client, auth_headers):
        with allure.step("Act: Send PUT request with new username"):
            response = client.put(
                "/api/v1/profile/me",
                headers=auth_headers,
                json={"username": "TEST UPDATE"},
            )
        with allure.step("Assert: Verify 200 OK"):
            assert response.status_code == 200

    @allure.title("API Validation errors on profile update")
    @allure.severity(allure.severity_level.NORMAL)
    def test_update_user_failed(self, client, auth_headers):
        with allure.step("Act: Send PUT request with invalid username (too short)"):
            response = client.put(
                "/api/v1/profile/me", headers=auth_headers, json={"username": "tes"}
            )
        with allure.step("Assert: Verify 422 Unprocessable Entity and error message"):
            assert response.status_code == 422
            json_data = response.get_json()
            assert "String should have at least 4 characters" in str(json_data)

    @allure.title("Fail to update profile without authorization")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_update_user_wo_auth(self, client):
        with allure.step("Act: Send PUT request without auth headers"):
            response = client.put("/api/v1/profile/me")

        with allure.step("Assert: Verify 401 Unauthorized"):
            assert response.status_code == 401


@allure.feature("Profile Management")
@allure.story("Delete Account")
@pytest.mark.usefixtures("db_session")
class TestDeleteAccount:

    @allure.title("Successfully delete user account")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_account_success(self, client, auth_headers, db_session):
        with allure.step("Act: Send DELETE request to /api/v1/profile/me"):
            response = client.delete("/api/v1/profile/me", headers=auth_headers)

        with allure.step("Assert: Verify 204 No Content"):
            assert response.status_code == 204

        with allure.step("Assert: Verify user is completely removed from DB"):
            deleted_user = (
                db_session.query(Users).filter_by(email="test@example.com").first()
            )
            assert deleted_user is None

    @allure.title("Fail to delete account without authorization")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_account_wo_auth(self, client):
        with allure.step("Act: Send DELETE request without auth headers"):
            response = client.delete("/api/v1/profile/me")

        with allure.step("Assert: Verify 401 Unauthorized"):
            assert response.status_code == 401

    @allure.title("Fail to delete non-existent account (Invalid Token ID)")
    @allure.severity(allure.severity_level.NORMAL)
    def test_delete_account_failed(self, client, auth_headers, db_session):
        with allure.step("Arrange: Generate fake token for non-existent user"):
            from flask_jwt_extended import create_access_token

            fake_token = create_access_token(identity="99999")
            fake_headers = {"Authorization": f"Bearer {fake_token}"}

        with allure.step("Act: Send DELETE request with fake token"):
            response = client.delete("/api/v1/profile/me", headers=fake_headers)

        with allure.step("Assert: Verify 404 Not Found"):
            assert response.status_code == 404


BASE_CHANGE_PASS_JSON = {
    "old_password": "ValidPassword123",
    "new_password": "TESTPASSWORD",
    "confirm_password": "TESTPASSWORD",
}

change_pass_failed_json = [
    (
        {
            "old_password": "321321",
            "new_password": "TESTPASSWORD",
            "confirm_password": "TESTPASSWORD",
        },
        401,
        "Invalid old password",
    ),
    (
        {
            "old_password": "ValidPassword123",
            "new_password": "EWRWRWRW",
            "confirm_password": "TESTPASSWORD",
        },
        422,
        "New password and confirmation do not match",
    ),
    (
        {
            "old_password": "ValidPassword123",
            "new_password": "ValidPassword123",
            "confirm_password": "ValidPassword123",
        },
        422,
        "New password cannot be the same as old password",
    ),
    ({}, 422, "Field required"),
]


@allure.feature("Profile Management")
@allure.story("Change Password")
@pytest.mark.usefixtures("db_session")
class TestChangePassword:

    @allure.title("Successfully change user password")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_change_password_success(self, client, auth_headers, db_session):
        with allure.step("Arrange: Set user password hash in DB to match old_password"):
            user = db_session.get(Users, 1)
            user.password_hash = generate_password_hash("ValidPassword123")
            db_session.commit()

        with allure.step("Act: Send POST request to change password"):
            response = client.post(
                "/api/v1/profile/change-password",
                headers=auth_headers,
                json=BASE_CHANGE_PASS_JSON,
            )
        with allure.step("Assert: Verify 200 OK"):
            assert response.status_code == 200

    @allure.title("API Validation errors on password change")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize(
        "test_data, expected_status, expected_error_fragment", change_pass_failed_json
    )
    def test_change_password_failed(
        self, client, auth_headers, test_data, expected_status, expected_error_fragment
    ):
        with allure.step("Act: Send POST request with invalid password payload"):
            response = client.post(
                "/api/v1/profile/change-password", headers=auth_headers, json=test_data
            )
        with allure.step(f"Assert: Verify status {expected_status} and error fragment"):
            assert response.status_code == expected_status
            json_data = response.get_json()
            assert expected_error_fragment in str(json_data)

    @allure.title("Fail to change password without authorization")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_change_password_wo_auth(self, client):
        with allure.step("Act: Send POST request without auth headers"):
            response = client.post(
                "/api/v1/profile/change-password", json=BASE_CHANGE_PASS_JSON
            )
        with allure.step("Assert: Verify 401 Unauthorized"):
            assert response.status_code == 401


@allure.feature("Profile Management")
@allure.story("Update Currency")
@pytest.mark.usefixtures("db_session")
class TestChangeCurrency:

    @allure.title("Successfully change user currency")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_change_currency_success(self, client, auth_headers):
        with allure.step("Act: Send PUT request with new currency payload"):
            response = client.put(
                "/api/v1/profile/me", headers=auth_headers, json={"currency": "UAH"}
            )
        with allure.step("Assert: Verify 200 OK"):
            assert response.status_code == 200

    @allure.title("Fail to change currency with invalid data")
    @allure.severity(allure.severity_level.NORMAL)
    def test_change_currency_failed(self, client, auth_headers):
        with allure.step("Act: Send PUT request with invalid currency string"):
            response = client.put(
                "/api/v1/profile/me",
                headers=auth_headers,
                json={"currency": "Invslid DATA"},
            )
        with allure.step("Assert: Verify 422 Unprocessable Entity"):
            assert response.status_code == 422

    @allure.title("Fail to change currency without authorization")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_change_currency_wo_auth(self, client):
        with allure.step("Act: Send PUT request without auth headers"):
            response = client.put("/api/v1/profile/me")

        with allure.step("Assert: Verify 401 Unauthorized"):
            assert response.status_code == 401


@allure.feature("Profile Management")
@allure.story("Monobank Token Management")
@pytest.mark.usefixtures("db_session")
class TestChangeToken:

    @allure.title("Successfully update Monobank token")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_change_token_success(self, client, auth_headers):
        with allure.step("Act: Send PUT request with valid token payload"):
            response = client.put(
                "/api/v1/profile/monobank",
                headers=auth_headers,
                json={"token": "1" * 44},
            )
        with allure.step("Assert: Verify 200 OK"):
            assert response.status_code == 200

    @allure.title("Fail to update Monobank token with invalid data length")
    @allure.severity(allure.severity_level.NORMAL)
    def test_change_token_failed(self, client, auth_headers):
        with allure.step("Act: Send PUT request with short/invalid token"):
            response = client.put(
                "/api/v1/profile/monobank", headers=auth_headers, json={"token": "TEST"}
            )
        with allure.step("Assert: Verify 422 Unprocessable Entity"):
            assert response.status_code == 422

    @allure.title("Fail to update Monobank token with empty payload")
    @allure.severity(allure.severity_level.NORMAL)
    def test_change_token_no_data(self, client, auth_headers):
        with allure.step("Act: Send PUT request with empty JSON object"):
            response = client.put(
                "/api/v1/profile/monobank", headers=auth_headers, json={}
            )
        with allure.step("Assert: Verify 422 Unprocessable Entity"):
            assert response.status_code == 422

    @allure.title("Fail to update Monobank token without authorization")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_change_token_wo_auth(self, client):
        with allure.step("Act: Send PUT request without auth headers"):
            response = client.put("/api/v1/profile/monobank", json={"token": "1" * 44})
        with allure.step("Assert: Verify 401 Unauthorized"):
            assert response.status_code == 401

    @allure.title("Successfully delete Monobank token")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_change_token_delete(self, client, auth_headers):
        with allure.step("Act: Send DELETE request to /api/v1/profile/monobank"):
            response = client.delete("/api/v1/profile/monobank", headers=auth_headers)
        with allure.step("Assert: Verify 204 No Content"):
            assert response.status_code == 204
