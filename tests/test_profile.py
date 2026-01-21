import pytest
from werkzeug.security import generate_password_hash

from tests.conftest import db_session
from finmate.models import Users

@pytest.mark.usefixtures("db_session")
class TestGetUser:

    def test_get_user_profile_success(self, client, auth_headers):
        response = client.get("/api/v1/profile/me", headers=auth_headers)
        assert response.status_code == 200


    def test_get_user_profile_wo_auth(self, client):
        response = client.get("/api/v1/profile/me")
        assert response.status_code == 401


@pytest.mark.usefixtures("db_session")
class TestUpdateUser:

    def test_update_user_success(self, client, auth_headers):
        response = client.put("/api/v1/profile/me",
                              headers=auth_headers,
                              json={"username": "TEST UPDATE"}
                              )
        assert response.status_code == 200


    def test_update_user_failed(self, client, auth_headers):
        response = client.put("/api/v1/profile/me",
                              headers=auth_headers,
                              json={"username": "tes"}
                              )
        assert response.status_code == 422
        json_data = response.get_json()
        assert "String should have at least 4 characters" in str(json_data)


    def test_update_user_wo_auth(self, client):
        response = client.put("/api/v1/profile/me")
        assert response.status_code == 401


@pytest.mark.usefixtures("db_session")
class TestDeleteAccount:

    def test_delete_account_success(self, client, auth_headers, db_session):
        response = client.delete("/api/v1/profile/me", headers=auth_headers)
        assert response.status_code == 204

        deleted_user = db_session.query(Users).filter_by(email="test@example.com").first()
        assert deleted_user is None


    def test_delete_account_wo_auth(self, client):
        response = client.delete("/api/v1/profile/me")
        assert response.status_code == 401


    def test_delete_account_failed(self, client, auth_headers, db_session):
        from flask_jwt_extended import create_access_token

        fake_token = create_access_token(identity="99999")
        fake_headers = {"Authorization": f"Bearer {fake_token}"}

        response = client.delete("/api/v1/profile/me", headers=fake_headers)
        assert response.status_code == 404


BASE_CHANGE_PASS_JSON ={
        "old_password": "ValidPassword123",
        "new_password": "TESTPASSWORD",
        "confirm_password": "TESTPASSWORD"
                        }


change_pass_failed_json = [
    (
        {
            "old_password": "321321",
            "new_password": "TESTPASSWORD",
            "confirm_password": "TESTPASSWORD"
        }, 401, "Invalid old password"
    ),
    (
        {
            "old_password": "ValidPassword123",
            "new_password": "EWRWRWRW",
            "confirm_password": "TESTPASSWORD"
        }, 422, "New password and confirmation do not match"
    ),
    (
        {
            "old_password": "ValidPassword123",
            "new_password": "ValidPassword123",
            "confirm_password": "ValidPassword123"
        }, 422, "New password cannot be the same as old password"
    ),
    (
        {}, 422, "Field required"
    )
]

@pytest.mark.usefixtures("db_session")
class TestChangePassword:

    def test_change_password_success(self, client,auth_headers, db_session):
        user = db_session.get(Users, 1)
        user.password_hash = generate_password_hash("ValidPassword123")
        db_session.commit()

        response = client.post("/api/v1/profile/change-password",
                              headers=auth_headers,
                              json=BASE_CHANGE_PASS_JSON
                              )
        assert response.status_code == 200


    @pytest.mark.parametrize(
        "test_data, expected_status, expected_error_fragment",
        change_pass_failed_json
    )
    def test_change_password_failed(self, client, auth_headers, test_data, expected_status, expected_error_fragment):
        response = client.post("/api/v1/profile/change-password",
                               headers=auth_headers,
                               json=test_data
                               )
        assert response.status_code == expected_status
        json_data = response.get_json()
        assert expected_error_fragment in str(json_data)


    def test_change_password_wo_auth(self, client):
        response = client.post("/api/v1/profile/change-password",
                               json=BASE_CHANGE_PASS_JSON
                               )
        assert response.status_code == 401


@pytest.mark.usefixtures("db_session")
class TestChangeCurrency:

    def test_change_currency_success(self, client, auth_headers):
        response = client.put("/api/v1/profile/me",
                              headers=auth_headers,
                              json={"currency": "UAH"}
                              )
        assert response.status_code == 200


    def test_change_currency_failed(self, client, auth_headers):
        response = client.put("/api/v1/profile/me",
                              headers=auth_headers,
                              json={"currency": "Invslid DATA"}
                              )
        assert response.status_code == 422


    def test_change_currency_wo_auth(self, client):
        response = client.put("/api/v1/profile/me")
        assert response.status_code == 401


@pytest.mark.usefixtures("db_session")
class TestChangeToken:

    def test_change_token_success(self, client, auth_headers):
        response = client.put("/api/v1/profile/monobank",
                              headers=auth_headers,
                              json={"token": "TESTMONOTOKEN"}
                              )
        assert response.status_code == 200


    def test_change_token_failed(self, client, auth_headers):
        response = client.put("/api/v1/profile/monobank",
                              headers=auth_headers,
                              json={"token": "TEST"}
                              )
        assert response.status_code == 422

    def test_change_token_no_data(self, client, auth_headers):
        response = client.put("/api/v1/profile/monobank",
                              headers=auth_headers,
                              json={}
                              )
        assert response.status_code == 422


    def test_change_token_wo_auth(self, client):
        response = client.put("/api/v1/profile/monobank",
                              json={"token": "TESTMONOTOKEN"}
                              )
        assert response.status_code == 401


#TODO: Test делит токен монобанка

