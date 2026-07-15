import allure
import pytest

BASE_CREATE_CAT_JSON = {"name": "TEST_CAT", "icon": "bi-wifi", "mcc_code": "1234, 7688"}

create_cat_failed_json = [
    ({}, 422, "Field required"),
    ({"name": ""}, 422, "String should have at least 1 character"),
    ({"name": 211}, 422, "Input should be a valid string"),
    (BASE_CREATE_CAT_JSON | {"mcc_code": 3}, 422, "Input should be a valid string"),
    ({"name": "T" * 51}, 422, "String should have at most 50 characters"),
    (
        BASE_CREATE_CAT_JSON | {"mcc_code": "T" * 129},
        422,
        "String should have at most 128 characters",
    ),
]


@allure.feature("Category Management")
@allure.story("Create Category")
class TestCreateCategory:

    @allure.title("Successfully create category via API")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_create_category_success(self, client, auth_headers):
        with allure.step("Act: Send POST request to /api/v1/categories/"):
            response = client.post(
                "/api/v1/categories/", headers=auth_headers, json=BASE_CREATE_CAT_JSON
            )
        with allure.step("Assert: Verify 201 Created"):
            assert response.status_code == 201

    @allure.title("Fail to create category with duplicate name")
    @allure.severity(allure.severity_level.NORMAL)
    def test_create_category_duplicate_name(self, client, auth_headers):
        with allure.step("Arrange: Create initial category"):
            client.post(
                "/api/v1/categories/", headers=auth_headers, json={"name": "UniqueName"}
            )

        with allure.step("Act: Attempt to create category with same name"):
            response = client.post(
                "/api/v1/categories/", headers=auth_headers, json={"name": "UniqueName"}
            )

        with allure.step("Assert: Verify 409 Conflict"):
            assert response.status_code == 409
            assert "already exists" in str(response.get_json())

    @allure.title("Fail to create category exceeding maximum limit")
    @allure.severity(allure.severity_level.NORMAL)
    def test_create_category_overlimit(self, client, auth_headers):
        with allure.step("Arrange: Fill category slots up to limit"):
            for i in range(4):
                response = client.post(
                    "/api/v1/categories/",
                    headers=auth_headers,
                    json={"name": f"Cat {i}"},
                )
                assert response.status_code == 201

        with allure.step("Act: Attempt to create one more category over the limit"):
            last_response = client.post(
                "/api/v1/categories/", headers=auth_headers, json={"name": "LAST CAT"}
            )
        with allure.step("Assert: Verify 400 Bad Request and limit error"):
            assert last_response.status_code == 400
            assert "limit" in str(last_response.get_json())

    @allure.title("API Validation errors on category creation")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize(
        "test_data, expected_status, expected_error_fragment", create_cat_failed_json
    )
    def test_create_category_failed(
        self, client, auth_headers, test_data, expected_status, expected_error_fragment
    ):
        with allure.step("Act: Send POST with invalid payload"):
            response = client.post(
                "/api/v1/categories/", headers=auth_headers, json=test_data
            )
        with allure.step(f"Assert: Verify status {expected_status} and error fragment"):
            assert response.status_code == expected_status
            json_data = response.get_json()
            assert expected_error_fragment in str(json_data)

    @allure.title("Fail to create category without authorization")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_category_wo_auth(self, client):
        with allure.step("Act: Send POST without auth headers"):
            response = client.post("/api/v1/categories/", json=BASE_CREATE_CAT_JSON)
        with allure.step("Assert: Verify 401 Unauthorized"):
            assert response.status_code == 401


update_cat_success_json = [{"name": "TEST_UPDATE", "mcc_code": ""}, {"mcc_code": "321"}]

update_cat_failed_json = [
    ({}, 400, "No data provided for update."),
    ({"name": ""}, 422, "String should have at least 1 character"),
    ({"name": 211}, 422, "Input should be a valid string"),
    ({"mcc_code": 3}, 422, "Input should be a valid string"),
    ({"name": "T" * 51}, 422, "String should have at most 50 characters"),
    ({"mcc_code": "T" * 129}, 422, "String should have at most 128 characters"),
]


@allure.feature("Category Management")
@allure.story("Update Category")
class TestUpdateCategory:

    @allure.title("Successfully update category via API")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize("test_data", update_cat_success_json)
    def test_update_category_success(self, client, auth_headers, test_data):
        with allure.step("Arrange: Create category to update"):
            response_post = client.post(
                "/api/v1/categories/", json=BASE_CREATE_CAT_JSON, headers=auth_headers
            )
            assert response_post.status_code == 201
            created_tx_id = response_post.get_json()["id"]

        with allure.step("Act: Send PUT request with new payload"):
            response = client.put(
                f"/api/v1/categories/{created_tx_id}",
                json=test_data,
                headers=auth_headers,
            )
        with allure.step("Assert: Verify 200 OK"):
            assert response.status_code == 200

    @allure.title("API Validation errors on category update")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize(
        "test_data, expected_status, expected_error_fragment", update_cat_failed_json
    )
    def test_update_category_failed(
        self, client, auth_headers, test_data, expected_status, expected_error_fragment
    ):
        with allure.step("Arrange: Create category to update"):
            response_post = client.post(
                "/api/v1/categories/", json=BASE_CREATE_CAT_JSON, headers=auth_headers
            )
            assert response_post.status_code == 201
            created_tx_id = response_post.get_json()["id"]

        with allure.step("Act: Send PUT request with invalid payload"):
            response = client.put(
                f"/api/v1/categories/{created_tx_id}",
                json=test_data,
                headers=auth_headers,
            )
        with allure.step(f"Assert: Verify status {expected_status} and error fragment"):
            assert response.status_code == expected_status
            json_data = response.get_json()
            assert expected_error_fragment in str(json_data)

    @allure.title("Fail to update category without authorization")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_update_category_wo_auth(self, client):
        with allure.step("Act: Send PUT request without auth headers"):
            response = client.put("/api/v1/categories/100")
        with allure.step("Assert: Verify 401 Unauthorized"):
            assert response.status_code == 401

    @allure.title("Fail to update non-existent category (404 Not Found)")
    @allure.severity(allure.severity_level.NORMAL)
    def test_update_category_perm_error(self, client, auth_headers):
        with allure.step("Act: Send PUT request to invalid ID"):
            response = client.put(
                "/api/v1/categories/100",
                headers=auth_headers,
                json={"name": "Check perm error"},
            )
        with allure.step("Assert: Verify 404 Not Found"):
            assert response.status_code == 404


@allure.feature("Category Management")
@allure.story("Delete Category")
class TestDeleteCategory:

    @allure.title("Successfully delete category via API")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_category_success(self, client, auth_headers):
        with allure.step("Arrange: Create category to delete"):
            response_post = client.post(
                "/api/v1/categories/", json=BASE_CREATE_CAT_JSON, headers=auth_headers
            )
            assert response_post.status_code == 201
            created_tx_id = response_post.get_json()["id"]

        with allure.step("Act: Send DELETE request"):
            response = client.delete(
                f"/api/v1/categories/{created_tx_id}", headers=auth_headers
            )

        with allure.step("Assert: Verify 204 No Content"):
            assert response.status_code == 204

    @allure.title("Fail to delete non-existent category")
    @allure.severity(allure.severity_level.NORMAL)
    def test_delete_category_failed(self, client, auth_headers):
        with allure.step("Act: Send DELETE request to invalid ID"):
            response = client.delete("/api/v1/categories/100", headers=auth_headers)
        with allure.step("Assert: Verify 404 Not Found"):
            assert response.status_code == 404

    @allure.title("Fail to delete category without authorization")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_transaction_wo_auth(self, client):
        with allure.step("Act: Send DELETE request without auth headers"):
            response = client.delete("/api/v1/categories/1")
        with allure.step("Assert: Verify 401 Unauthorized"):
            assert response.status_code == 401


@allure.feature("Category Management")
@allure.story("Retrieve Categories")
class TestGetCategories:

    @allure.title("Successfully retrieve all categories")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_get_all_categories_success(self, client, auth_headers):
        with allure.step("Act: Send GET request to /api/v1/categories/all"):
            response = client.get("/api/v1/categories/all", headers=auth_headers)
        with allure.step("Assert: Verify 200 OK"):
            assert response.status_code == 200

    @allure.title("Fail to retrieve categories without authorization")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_all_categories_wo_auth(self, client):
        with allure.step("Act: Send GET request without auth headers"):
            response = client.get("/api/v1/categories/all")
        with allure.step("Assert: Verify 401 Unauthorized"):
            assert response.status_code == 401
