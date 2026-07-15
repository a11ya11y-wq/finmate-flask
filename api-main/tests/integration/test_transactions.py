import allure
import pytest

BASE_TRANSACTION_JSON = {
    "amount": 100.0,
    "title": "TEST_TITLE",
    "transaction_type": "expense",
    "category_id": 1,
}

create_tx_success_json = [
    (BASE_TRANSACTION_JSON | {"amount": 100}),
    (BASE_TRANSACTION_JSON | {"transaction_type": "income"}),
    (BASE_TRANSACTION_JSON | {"note": "TEST NOTE"}),
    (BASE_TRANSACTION_JSON | {"created_at": "2025-11-10T14:30:00+02:00"}),
    (BASE_TRANSACTION_JSON | {"created_at": "2025-11-15"}),
]

create_tx_failed_json = [
    (BASE_TRANSACTION_JSON | {"amount": -100}, 422, "Input should be greater than 0"),
    (
        BASE_TRANSACTION_JSON | {"transaction_type": "ANOTHER TYPE"},
        422,
        " Input should be 'income' or 'expense'",
    ),
    (
        BASE_TRANSACTION_JSON | {"category_id": "INCORRECT CAT_ID"},
        422,
        "Input should be a valid integer",
    ),
    (
        BASE_TRANSACTION_JSON | {"created_at": "2027-22-22"},
        422,
        "month value is outside expected range of 1-12",
    ),
    (
        BASE_TRANSACTION_JSON | {"created_at": "2027-10-46"},
        422,
        "Input should be a valid datetime or date",
    ),
    (
        BASE_TRANSACTION_JSON | {"created_at": "2027+12+10"},
        422,
        "invalid date separator",
    ),
    (
        BASE_TRANSACTION_JSON | {"created_at": "0-12-10"},
        422,
        "Input should be a valid datetime or date, input is too short",
    ),
    (
        BASE_TRANSACTION_JSON | {"created_at": "NOT VALID DATE"},
        422,
        "Input should be a valid datetime or date",
    ),
    (
        BASE_TRANSACTION_JSON | {"category_id": 100},
        404,
        "Category 100 not found or access denied.",
    ),
    (
        BASE_TRANSACTION_JSON | {"amount": "NOT VALID AMOUNT"},
        422,
        "Input should be a valid decimal",
    ),
    ({}, 422, "Field required"),
    (
        BASE_TRANSACTION_JSON | {"amount": 123456789},
        422,
        "Decimal input should have no more than 8 digits before the decimal point",
    ),
    (
        BASE_TRANSACTION_JSON | {"amount": 100.123},
        422,
        "Decimal input should have no more than 2 decimal places",
    ),
    (
        BASE_TRANSACTION_JSON | {"title": "T" * 51},
        422,
        "String should have at most 50 characters",
    ),
    (
        BASE_TRANSACTION_JSON | {"note": "N" * 129},
        422,
        "String should have at most 128 characters",
    ),
]


@allure.feature("Transaction Management")
@allure.story("Create Transaction")
@pytest.mark.usefixtures("db_session")
class TestCreateTransactions:

    @allure.title("Successfully create transaction via API")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.parametrize("test_data", create_tx_success_json)
    def test_create_transaction_success(self, client, auth_headers, test_data):
        with allure.step("Act: Send POST request to create transaction"):
            response = client.post(
                "/api/v1/transactions/", json=test_data, headers=auth_headers
            )
        with allure.step("Assert: Verify 201 Created and title match"):
            assert response.status_code == 201
            json_data = response.get_json()
            assert json_data["title"] == "TEST_TITLE"

    @allure.title("API Validation errors on transaction creation")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize(
        "test_data, expected_status, expected_error_fragment", create_tx_failed_json
    )
    def test_create_transaction_failed(
        self, client, auth_headers, test_data, expected_status, expected_error_fragment
    ):
        with allure.step("Act: Send POST request with invalid payload"):
            response = client.post(
                "/api/v1/transactions/", json=test_data, headers=auth_headers
            )
        with allure.step(f"Assert: Verify status {expected_status} and error fragment"):
            assert response.status_code == expected_status
            json_data = response.get_json()
            assert expected_error_fragment in str(json_data)

    @allure.title("Fail to create transaction without authorization")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_transaction_wo_auth(self, client):
        with allure.step("Act: Send POST request without auth headers"):
            response = client.post(
                "/api/v1/transactions/",
                json=BASE_TRANSACTION_JSON,
            )
        with allure.step("Assert: Verify 401 Unauthorized"):
            assert response.status_code == 401


update_tx_success_json = [
    {"amount": "50"},
    {"title": "UPDATED_TITLE"},
    {"transaction_type": "income"},
    {"category_id": "2"},
    {"note": "TEST NOTE"},
    {"created_at": "2025-11-15"},
    {"created_at": "2025-11-10T14:30:00+02:00"},
    {
        "amount": 200,
        "title": "TITLE TEST",
        "transaction_type": "income",
        "category_id": "3",
        "note": "TEST NOTE",
        "created_at": "2025-11-15",
    },
]

update_tx_failed_json = [
    ({"amount": "FAKE"}, 422, "Input should be a valid decimal"),
    ({"amount": -10}, 422, "Input should be greater than 0"),
    ({"title": ""}, 422, "String should have at least 1 character"),
    (
        {"transaction_type": "INVALID TYPE"},
        422,
        "Input should be 'income' or 'expense'",
    ),
    ({"category_id": "INVALID DATA"}, 422, "Input should be a valid integer"),
    ({"category_id": 100}, 404, "Category 100 not found or access denied"),
    (
        {"created_at": "0-11-15"},
        422,
        "Input should be a valid datetime or date, input is too short",
    ),
    (
        {"created_at": "2025+11-15"},
        422,
        "Input should be a valid datetime or date, invalid date separator",
    ),
    (
        {"created_at": "2025-15-15"},
        422,
        "Input should be a valid datetime or date, month value is outside expected range of 1-12",
    ),
    (
        {"created_at": "2025-11-40"},
        422,
        "Input should be a valid datetime or date, day value is outside expected range",
    ),
    (
        {"created_at": "INVALID DATA"},
        422,
        "Input should be a valid datetime or date, invalid character in year",
    ),
    (
        {"amount": 123456789.0},
        422,
        "Decimal input should have no more than 8 digits before the decimal point",
    ),
    (
        {"amount": 100.123},
        422,
        "Decimal input should have no more than 2 decimal places",
    ),
    ({"title": "T" * 51}, 422, "String should have at most 50 characters"),
    ({"note": "N" * 129}, 422, "String should have at most 128 characters"),
    ({}, 400, "No valid fields to update."),
]


@allure.feature("Transaction Management")
@allure.story("Update Transaction")
@pytest.mark.usefixtures("db_session")
class TestUpdateTransactions:

    @allure.title("Successfully update transaction via API")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize("test_data", update_tx_success_json)
    def test_update_transaction_success(self, client, auth_headers, test_data):
        with allure.step("Arrange: Create transaction to update"):
            response_post = client.post(
                "/api/v1/transactions/",
                json=BASE_TRANSACTION_JSON,
                headers=auth_headers,
            )
            assert response_post.status_code == 201
            created_tx_id = response_post.get_json()["id"]

        with allure.step("Act: Send PUT request with update payload"):
            response = client.put(
                f"/api/v1/transactions/{created_tx_id}",
                json=test_data,
                headers=auth_headers,
            )
        with allure.step("Assert: Verify 200 OK"):
            assert response.status_code == 200

    @allure.title("Fail to update transaction without authorization")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_update_transaction_wo_auth(self, client):
        with allure.step("Act: Send PUT request without auth headers"):
            response = client.put("/api/v1/transactions/1")
        with allure.step("Assert: Verify 401 Unauthorized"):
            assert response.status_code == 401

    @allure.title("API Validation errors on transaction update")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize(
        "test_data, expected_status, expected_error_fragment", update_tx_failed_json
    )
    def test_update_transaction_failed(
        self, client, auth_headers, test_data, expected_status, expected_error_fragment
    ):
        with allure.step("Arrange: Create transaction to update"):
            response_post = client.post(
                "/api/v1/transactions/",
                json=BASE_TRANSACTION_JSON,
                headers=auth_headers,
            )
            assert response_post.status_code == 201
            created_tx_id = response_post.get_json()["id"]

        with allure.step("Act: Send PUT request with invalid payload"):
            response = client.put(
                f"/api/v1/transactions/{created_tx_id}",
                json=test_data,
                headers=auth_headers,
            )
        with allure.step(f"Assert: Verify status {expected_status} and error fragment"):
            assert response.status_code == expected_status
            json_data = response.get_json()
            assert expected_error_fragment in str(json_data)


@allure.feature("Transaction Management")
@allure.story("Delete Transaction")
@pytest.mark.usefixtures("db_session")
class TestDeleteTransactions:

    @allure.title("Successfully delete transaction via API")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_transaction_success(self, client, auth_headers):
        with allure.step("Arrange: Create transaction to delete"):
            response_post = client.post(
                "/api/v1/transactions/",
                json=BASE_TRANSACTION_JSON,
                headers=auth_headers,
            )
            assert response_post.status_code == 201
            created_tx_id = response_post.get_json()["id"]

        with allure.step("Act: Send DELETE request"):
            response = client.delete(
                f"/api/v1/transactions/{created_tx_id}", headers=auth_headers
            )

        with allure.step("Assert: Verify 204 No Content"):
            assert response.status_code == 204

    @allure.title("Fail to delete non-existent transaction")
    @allure.severity(allure.severity_level.NORMAL)
    def test_delete_transaction_failed(self, client, auth_headers):
        with allure.step("Act: Send DELETE request for invalid ID"):
            response = client.delete("/api/v1/transactions/100", headers=auth_headers)
        with allure.step("Assert: Verify 404 Not Found"):
            assert response.status_code == 404

    @allure.title("Fail to delete transaction without authorization")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_transaction_wo_auth(self, client):
        with allure.step("Act: Send DELETE request without auth headers"):
            response = client.delete("/api/v1/transactions/1")
        with allure.step("Assert: Verify 401 Unauthorized"):
            assert response.status_code == 401


@allure.feature("Transaction Management")
@allure.story("Retrieve Transaction")
class TestGetTransactions:

    @allure.title("Successfully retrieve transaction by ID")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_get_transaction_success(self, client, auth_headers):
        with allure.step("Arrange: Create transaction to retrieve"):
            response_post = client.post(
                "/api/v1/transactions/",
                json=BASE_TRANSACTION_JSON,
                headers=auth_headers,
            )
            assert response_post.status_code == 201
            created_tx_id = response_post.get_json()["id"]

        with allure.step("Act: Send GET request"):
            response = client.get(
                f"/api/v1/transactions/{created_tx_id}", headers=auth_headers
            )

        with allure.step("Assert: Verify 200 OK"):
            assert response.status_code == 200

    @allure.title("Fail to retrieve non-existent transaction")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_transaction_failed(self, client, auth_headers):
        with allure.step("Act: Send GET request to invalid ID"):
            response = client.get("/api/v1/transactions/1", headers=auth_headers)
        with allure.step("Assert: Verify 404 Not Found"):
            assert response.status_code == 404

    @allure.title("Fail to retrieve transaction without authorization")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_transaction_wo_auth(self, client):
        with allure.step("Act: Send GET request without auth headers"):
            response = client.get("/api/v1/transactions/1")
        with allure.step("Assert: Verify 401 Unauthorized"):
            assert response.status_code == 401
