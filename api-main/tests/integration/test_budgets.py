import allure
import pytest

BASE_BUDGET_JSON = {"amount": "1000", "category_id": 1, "is_recurring": True}

create_bud_failed_json = [
    # Negative amount (Validation)
    (BASE_BUDGET_JSON | {"amount": -100}, 422, "Input should be greater than 0"),
    # Incorrect tx_type (Validation)
    (
        BASE_BUDGET_JSON | {"is_recurring": "ANOTHER TYPE"},
        422,
        "Input should be a valid boolean, unable to interpret input",
    ),
    # Incorrect cat_id -> str (Validation)
    (
        BASE_BUDGET_JSON | {"category_id": "INCORRECT CAT_ID"},
        422,
        "Input should be a valid integer",
    ),
    # Not valid cat_id (Service)
    (
        BASE_BUDGET_JSON | {"category_id": 100},
        404,
        "Category 100 not found or access denied.",
    ),
    # Not valid amount (Validation)
    (
        BASE_BUDGET_JSON | {"amount": "NOT VALID AMOUNT"},
        422,
        "Input should be a valid decimal",
    ),
    ({}, 422, "Field required"),
    # Exceeding amount digits limit
    (
        BASE_BUDGET_JSON | {"amount": 123456789},
        422,
        "Decimal input should have no more than 8 digits before the decimal point",
    ),
    # Exceeding amount decimal places limit
    (
        BASE_BUDGET_JSON | {"amount": 100.123},
        422,
        "Decimal input should have no more than 2 decimal places",
    ),
]


@allure.feature("Budget Management")
@allure.story("Create Budget")
class TestCreateBudgets:

    @allure.title("Successfully create budget via API")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_create_budgets_success(self, client, auth_headers):
        with allure.step("Act: Send POST to /api/v1/budgets/ with valid data"):
            response = client.post(
                "/api/v1/budgets/", headers=auth_headers, json=BASE_BUDGET_JSON
            )
        with allure.step("Assert: Verify 201 Created"):
            assert response.status_code == 201

    @allure.title("API Validation errors on budget creation")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize(
        "test_data, expected_status, expected_error_fragment", create_bud_failed_json
    )
    def test_create_budgets_failed(
        self, client, auth_headers, test_data, expected_status, expected_error_fragment
    ):
        with allure.step("Act: Send POST to /api/v1/budgets/ with invalid data"):
            response = client.post(
                "/api/v1/budgets/", headers=auth_headers, json=test_data
            )
        with allure.step(f"Assert: Verify status {expected_status} and error message"):
            assert response.status_code == expected_status
            json_data = response.get_json()
            assert expected_error_fragment in str(json_data)

    @allure.title("Fail to create budget without authorization")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_budgets_wo_auth(self, client):
        with allure.step("Act: Send POST without auth headers"):
            response = client.post("/api/v1/budgets/", json=BASE_BUDGET_JSON)
        with allure.step("Assert: Verify 401 Unauthorized"):
            assert response.status_code == 401

    @allure.title("Fail to create budget exceeding maximum limit")
    @allure.severity(allure.severity_level.NORMAL)
    def test_create_budgets_overlimit(self, client, auth_headers):
        with allure.step("Arrange: Fetch existing categories and fill budget limits"):
            response = client.get("/api/v1/categories/all", headers=auth_headers)
            assert response.status_code == 200
            response_json = response.json
            existing_categories = response_json["data"]

            assert len(existing_categories) >= 6

            for i in range(5):
                cat_id = existing_categories[i]["id"]
                response = client.post(
                    "/api/v1/budgets/",
                    headers=auth_headers,
                    json={
                        "amount": "1000",
                        "category_id": cat_id,
                        "is_recurring": True,
                    },
                )
                assert response.status_code == 201

            extra_cat_id = existing_categories[5]["id"]

        with allure.step("Act: Attempt to create one budget over the limit"):
            last_response = client.post(
                "/api/v1/budgets/",
                headers=auth_headers,
                json={"amount": 100, "category_id": extra_cat_id, "is_recurring": True},
            )
        with allure.step("Assert: Verify 400 Bad Request and limit error"):
            assert last_response.status_code == 400
            assert "limit" in str(last_response.get_json())


BASE_UPDATE_JSON = {"amount": "500", "category_id": 1, "is_recurring": False}

update_bud_failed = [
    # Negative amount (Validation)
    (BASE_UPDATE_JSON | {"amount": -100}, 422, "Input should be greater than 0"),
    # Incorrect tx_type (Validation)
    (
        BASE_UPDATE_JSON | {"is_recurring": "ANOTHER TYPE"},
        422,
        "Input should be a valid boolean, unable to interpret input",
    ),
    # Incorrect cat_id -> str (Validation)
    (
        BASE_UPDATE_JSON | {"category_id": "INCORRECT CAT_ID"},
        422,
        "Input should be a valid integer",
    ),
    # Not valid cat_id (Service)
    (
        BASE_UPDATE_JSON | {"category_id": 100},
        404,
        "Category 100 not found or access denied.",
    ),
    # Not valid amount (Validation)
    (
        BASE_UPDATE_JSON | {"amount": "NOT VALID AMOUNT"},
        422,
        "Input should be a valid decimal",
    ),
    ({}, 422, "Field required"),
    # Exceeding amount digits limit
    (
        BASE_UPDATE_JSON | {"amount": 123456789},
        422,
        "Decimal input should have no more than 8 digits before the decimal point",
    ),
    # Exceeding amount decimal places limit
    (
        BASE_UPDATE_JSON | {"amount": 100.123},
        422,
        "Decimal input should have no more than 2 decimal places",
    ),
]


@allure.feature("Budget Management")
@allure.story("Update Budget")
class TestUpdateBudgets:

    @allure.title("Successfully update existing budget via API")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_update_budgets_success(self, client, auth_headers):
        with allure.step("Arrange: Create initial budget"):
            response_post = client.post(
                "/api/v1/budgets/", headers=auth_headers, json=BASE_BUDGET_JSON
            )
            assert response_post.status_code == 201

        with allure.step("Act: Send POST (Update) with new payload"):
            response = client.post(
                "/api/v1/budgets/", headers=auth_headers, json=BASE_UPDATE_JSON
            )
        with allure.step("Assert: Verify 200 OK"):
            assert response.status_code == 200

    @allure.title("API Validation errors on budget update")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize(
        "test_data, expected_status, expected_error_fragment", update_bud_failed
    )
    def test_update_budgets_failed(
        self, client, auth_headers, test_data, expected_status, expected_error_fragment
    ):
        with allure.step("Arrange: Create initial budget"):
            response_post = client.post(
                "/api/v1/budgets/", headers=auth_headers, json=BASE_BUDGET_JSON
            )
            assert response_post.status_code == 201

        with allure.step("Act: Send POST (Update) with invalid payload"):
            response = client.post(
                "/api/v1/budgets/", headers=auth_headers, json=test_data
            )
        with allure.step(f"Assert: Verify status {expected_status} and error message"):
            assert response.status_code == expected_status
            json_data = response.get_json()
            assert expected_error_fragment in str(json_data)

    @allure.title("Fail to update budget without authorization")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_update_budgets_wo_auth(self, client, auth_headers):
        with allure.step("Act: Send POST (Update) without auth headers"):
            response = client.post("/api/v1/budgets/", json=BASE_UPDATE_JSON)
        with allure.step("Assert: Verify 401 Unauthorized"):
            assert response.status_code == 401


@allure.feature("Budget Management")
@allure.story("Delete Budget")
class TestDeleteBudgets:

    @allure.title("Successfully delete budget via API")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_budgets_success(self, client, auth_headers):
        with allure.step("Arrange: Create budget to delete"):
            response_post = client.post(
                "/api/v1/budgets/", headers=auth_headers, json=BASE_BUDGET_JSON
            )
            created_bud_id = response_post.get_json()["id"]

        with allure.step("Act: Send DELETE request"):
            response = client.delete(
                f"/api/v1/budgets/{created_bud_id}", headers=auth_headers
            )

        with allure.step("Assert: Verify 204 No Content"):
            assert response.status_code == 204

    @allure.title("Fail to delete non-existent budget")
    @allure.severity(allure.severity_level.NORMAL)
    def test_delete_budgets_failed(self, client, auth_headers):
        with allure.step("Act: Send DELETE request for invalid ID"):
            response = client.delete("/api/v1/budgets/100", headers=auth_headers)
        with allure.step("Assert: Verify 404 Not Found"):
            assert response.status_code == 404

    @allure.title("Fail to delete budget without authorization")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_budgets_wo_auth(self, client):
        with allure.step("Act: Send DELETE request without auth headers"):
            response = client.delete("/api/v1/budgets/100")
        with allure.step("Assert: Verify 401 Unauthorized"):
            assert response.status_code == 401


@allure.feature("Budget Management")
@allure.story("Retrieve Budgets")
class TestGetBudgets:

    @allure.title("Successfully retrieve all budgets with calculated stats")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_get_all_budgets_success(self, client, auth_headers):
        with allure.step("Arrange: Create budget and related transactions"):
            client.post("/api/v1/budgets/", headers=auth_headers, json=BASE_BUDGET_JSON)
            client.post(
                "/api/v1/transactions/",
                headers=auth_headers,
                json={
                    "amount": 250,
                    "title": "Groceries",
                    "transaction_type": "expense",
                    "category_id": 1,
                },
            )
            client.post(
                "/api/v1/transactions/",
                headers=auth_headers,
                json={
                    "amount": 250,
                    "title": "More Food",
                    "transaction_type": "expense",
                    "category_id": 1,
                },
            )

        with allure.step("Act: Send GET request to /api/v1/budgets/"):
            response = client.get("/api/v1/budgets/", headers=auth_headers)

        with allure.step(
            "Assert: Verify stats aggregation (total_spent, remaining, percentage)"
        ):
            assert response.status_code == 200
            data = response.get_json()

            assert len(data) == 1
            budget_stat = data[0]

            assert budget_stat["total_spent"] == 500.0
            assert budget_stat["remaining"] == 500.0
            assert budget_stat["percentage"] == 50.0

            assert "day" in budget_stat["deadline_info"]
            assert "left" in budget_stat["deadline_info"]

    @allure.title("Fail to retrieve budgets without authorization")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_all_budgets_wo_auth(self, client):
        with allure.step("Act: Send GET request without auth headers"):
            response = client.get("/api/v1/budgets/")
        with allure.step("Assert: Verify 401 Unauthorized"):
            assert response.status_code == 401

    # TODO: Додати перевірку ізоляції данних
