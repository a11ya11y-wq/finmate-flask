import pytest


BASE_TRANSACTION_JSON = {
    "amount": 100.0,
    "title": "TEST_TITLE",
    "transaction_type": "expense",
    "category_id": 1,
}

create_tx_success_json = [
    # Amount -> int
    (
        BASE_TRANSACTION_JSON | {"amount": 100}
    ),
    # Another tx_type
    (
        BASE_TRANSACTION_JSON | {"transaction_type": "income"}
    ),
    # With note
    (
        BASE_TRANSACTION_JSON | {"note": "TEST NOTE"}
    ),
    # with created_at with timezone
    (
        BASE_TRANSACTION_JSON | {"created_at": "2025-11-10T14:30:00+02:00"}
    ),
# with created_at wo timezone
    (
        BASE_TRANSACTION_JSON | {"created_at": "2025-11-15"}
    )
]

create_tx_failed_json =[
    # Negative amount (Validation)
    (
        BASE_TRANSACTION_JSON | {"amount": -100},
        400,
        "Input should be greater than 0"
    ),
    # Incorrect tx_type (Validation)
    (
        BASE_TRANSACTION_JSON | {"transaction_type": "ANOTHER TYPE"},
        400,
        "Input should be \\\'income\\\' or \\\'expense\\\'"
    ),
    # Incorrect cat_id -> str (Validation)
    (
        BASE_TRANSACTION_JSON | {"category_id": "INCORRECT CAT_ID"},
        400,
        "Input should be a valid integer"
    ),
    # Incorrect month in created_at (Validation)
    (
        BASE_TRANSACTION_JSON | {"created_at": "2027-22-22"},
        400,
        "month value is outside expected range of 1-12"
    ),
    # Incorrect date in created_at (Validation)
    (
        BASE_TRANSACTION_JSON | {"created_at": "2027-10-46"},
        400,
        "Input should be a valid datetime or date"
    ),
    # Incorrect separator in created_at (Validation)
    (
      BASE_TRANSACTION_JSON | {"created_at": "2027+12+10"},
        400,
        "invalid date separator"
    ),
    # Short year in created_at
    (
      BASE_TRANSACTION_JSON | {"created_at": "0-12-10"},
        400,
        "Input should be a valid datetime or date, input is too short"
    ),
    # Incorrect created_at (Validation)
    (
        BASE_TRANSACTION_JSON | {"created_at": "NOT VALID DATE"},
        400,
        "Input should be a valid datetime or date"
    ),
    # Not valid cat_id (Service)
    (
        BASE_TRANSACTION_JSON | {"category_id": 100},
        403,
        "Category 100 not found or access denied."
    ),
    # Not valid amount (Validation)
    (
        BASE_TRANSACTION_JSON | {"amount": "NOT VALID AMOUNT"},
        400,
        "Input should be a valid decimal"
    ),
    (
        {}, 400, "No JSON data provided"
    )
]

@pytest.mark.usefixtures("db_session")
class TestCreateTransactions:


    @pytest.mark.parametrize(
        "test_data", create_tx_success_json
    )
    def test_create_transaction_success(self, client, auth_headers, test_data):
        response = client.post("/api/v1/transactions/",
                               json=test_data,
                               headers=auth_headers
                               )
        assert response.status_code == 201
        json_data = response.get_json()
        assert json_data['title'] == "TEST_TITLE"


    @pytest.mark.parametrize(
        "test_data, expected_status, expected_error_fragment",
        create_tx_failed_json
    )
    def test_create_transaction_failed(self, client, auth_headers, test_data, expected_status, expected_error_fragment):
        response = client.post("/api/v1/transactions/",
                               json=test_data,
                               headers=auth_headers
                               )
        assert response.status_code == expected_status
        json_data = response.get_json()
        assert expected_error_fragment in str(json_data)

    def test_create_transaction_wo_auth(self,client):
        response = client.post("/api/v1/transactions/",
                               json=BASE_TRANSACTION_JSON,
                               )
        assert response.status_code == 401

update_tx_success_json = [
    {"amount": "50"},
    {"title": "UPDATED_TITLE"},
    {"transaction_type": "income"},
    {"category_id": "2"},
    {"note": "TEST NOTE"},
    {"created_at": "2025-11-15"},
    {"created_at": "2025-11-10T14:30:00+02:00"},
    (
        {
            "amount": 200,
            "title": "TITLE TEST",
            "transaction_type": "income",
            "category_id": "3",
            "note": "TEST NOTE",
            "created_at": "2025-11-15"
        }
    )
]

update_tx_failed_json = [
    ({"amount": "FAKE"}, 400, "'Input should be a valid decimal"),
    ({"amount": -10}, 400, "Input should be greater than 0"),
    ({"title": ""}, 400, "String should have at least 1 character"),
    ({"transaction_type": "INVALID TYPE"}, 400, "Input should be \\\'income\\\' or \\\'expense\\\'"),
    ({"category_id": "INVALID DATA"}, 400, "Input should be a valid integer"),
    ({"category_id": 100}, 403, "Category 100 not found or access denied"),
    ({"created_at": "0-11-15"}, 400, "Input should be a valid datetime or date, input is too short"),
    ({"created_at": "2025+11-15"}, 400, "Input should be a valid datetime or date, invalid date separator"),
    ({"created_at": "2025-15-15"}, 400, "Input should be a valid datetime or date, month value is outside expected range of 1-12"),
    ({"created_at": "2025-11-40"}, 400, "Input should be a valid datetime or date, day value is outside expected range"),
    ({"created_at": "INVALID DATA"}, 400, "Input should be a valid datetime or date, invalid character in year"),
    ({}, 400, "No JSON data provided")
]

@pytest.mark.usefixtures("db_session")
class TestUpdateTransactions:

    @pytest.mark.parametrize(
        "test_data",update_tx_success_json
    )
    def test_update_transaction_success(self, client, auth_headers, test_data):
        response_post = client.post("/api/v1/transactions/",
                               json=BASE_TRANSACTION_JSON,
                               headers=auth_headers
                               )
        assert response_post.status_code == 201
        created_tx_id = response_post.get_json()['id']

        response = client.put(f"/api/v1/transactions/{created_tx_id}",
                              json=test_data,
                              headers=auth_headers
                              )
        assert response.status_code == 200


    def test_update_transaction_wo_auth(self, client):
        response = client.put("/api/v1/transactions/1")
        assert response.status_code == 401


    @pytest.mark.parametrize(
        "test_data, expected_status, expected_error_fragment",
        update_tx_failed_json
    )
    def test_update_transaction_failed(self, client, auth_headers, test_data, expected_status, expected_error_fragment):
        response_post = client.post("/api/v1/transactions/",
                                    json=BASE_TRANSACTION_JSON,
                                    headers=auth_headers
                                    )
        assert response_post.status_code == 201
        created_tx_id = response_post.get_json()['id']

        response = client.put(f"/api/v1/transactions/{created_tx_id}",
                              json=test_data,
                              headers=auth_headers
                              )
        assert response.status_code == expected_status
        json_data = response.get_json()
        assert expected_error_fragment in str(json_data)



@pytest.mark.usefixtures("db_session")
class TestDeleteTransactions:

    def test_delete_transaction_success(self, client, auth_headers):
        response_post = client.post("/api/v1/transactions/",
                                    json=BASE_TRANSACTION_JSON,
                                    headers=auth_headers
                                    )
        assert response_post.status_code == 201
        created_tx_id = response_post.get_json()['id']

        response = client.delete(f"/api/v1/transactions/{created_tx_id}", headers=auth_headers)
        assert response.status_code == 204

    def test_delete_transaction_failed(self, client, auth_headers):
        response = client.delete("/api/v1/transactions/100", headers=auth_headers)
        assert response.status_code == 403

    def test_delete_transaction_wo_auth(self, client):
        response = client.delete("/api/v1/transactions/1")
        assert response.status_code == 401


class TestGetTransactions:

    def test_get_transaction_success(self, client, auth_headers):
        response_post = client.post("/api/v1/transactions/",
                                   json=BASE_TRANSACTION_JSON,
                                   headers=auth_headers
                                   )
        assert response_post.status_code == 201
        created_tx_id = response_post.get_json()['id']

        response = client.get(f"/api/v1/transactions/{created_tx_id}",  headers=auth_headers)
        assert response.status_code == 200

    def test_get_transaction_failed(self, client, auth_headers):
        response = client.get("/api/v1/transactions/1",  headers=auth_headers)
        assert response.status_code == 403

    def test_get_transaction_wo_auth(self, client):
        response = client.get("/api/v1/transactions/1")
        assert response.status_code == 401