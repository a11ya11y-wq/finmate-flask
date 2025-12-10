import pytest


BASE_CREATE_CAT_JSON = {
    "name": "TEST_CAT",
    "mcc_code": "1234, 7688"
}

create_cat_failed_json = [
    (
        {}, 422, "Field required"
    ),
    (
        {"name": ""}, 422, "String should have at least 1 character"
    ),
    (
        {"name": 211}, 422, "Input should be a valid string"
    ),
    (
        BASE_CREATE_CAT_JSON | {"mcc_code": 3}, 422, "Input should be a valid string"
    )
]

class TestCreateCategory:

    def test_create_category_success(self, client, auth_headers):
        response = client.post("/api/v1/categories/",
                                    headers=auth_headers,
                                    json=BASE_CREATE_CAT_JSON
                                    )
        assert response.status_code == 201

    def test_create_category_duplicate_name(self, client, auth_headers):
        client.post("/api/v1/categories/", headers=auth_headers, json={"name": "UniqueName"})

        response = client.post("/api/v1/categories/", headers=auth_headers, json={"name": "UniqueName"})

        assert response.status_code == 409
        assert "already exists" in str(response.get_json())

    def test_create_category_overlimit(self, client, auth_headers):
        for i in range(3):
            response = client.post("/api/v1/categories/", headers=auth_headers, json={"name": f"Cat {i}"})
            assert response.status_code == 201

        last_response = client.post("/api/v1/categories/",
                                    headers=auth_headers,
                                    json={"name": "LAST CAT"}
                                    )
        assert last_response.status_code == 400
        assert "limit" in str(last_response.get_json())



    @pytest.mark.parametrize(
        "test_data, expected_status, expected_error_fragment",
        create_cat_failed_json
    )
    def test_create_category_failed(self, client, auth_headers, test_data, expected_status, expected_error_fragment):
        response = client.post("/api/v1/categories/",
                                    headers=auth_headers,
                                    json=test_data
                                    )
        assert response.status_code == expected_status

        json_data = response.get_json()
        assert expected_error_fragment in str(json_data)

    def test_create_category_wo_auth(self, client):
        response = client.post("/api/v1/categories/", json=BASE_CREATE_CAT_JSON)
        assert response.status_code == 401


update_cat_success_json = [
    {"name": "TEST_UPDATE", "mcc_code": ""},
    {"mcc_code": "321"}
]

update_cat_failed_json = [
    (
        {}, 400, "No data provided for update."
    ),
    (
        {"name": ""}, 422, "String should have at least 1 character"
    ),
    (
        {"name": 211}, 422, "Input should be a valid string"
    ),
    (
        {"mcc_code": 3}, 422, "Input should be a valid string"
    )
]

class TestUpdateCategory:

    @pytest.mark.parametrize(
        "test_data", update_cat_success_json
    )
    def test_update_category_success(self, client, auth_headers, test_data):
        response_post = client.post("/api/v1/categories/",
                                    json=BASE_CREATE_CAT_JSON,
                                    headers=auth_headers
                                    )
        assert response_post.status_code == 201
        created_tx_id = response_post.get_json()['id']

        response = client.put(f"/api/v1/categories/{created_tx_id}",
                                    json=test_data,
                                    headers=auth_headers
                                    )
        assert response.status_code == 200

    @pytest.mark.parametrize(
        "test_data, expected_status, expected_error_fragment",
        update_cat_failed_json
    )
    def test_update_category_failed(self, client, auth_headers, test_data, expected_status, expected_error_fragment):
        response_post = client.post("/api/v1/categories/",
                                    json=BASE_CREATE_CAT_JSON,
                                    headers=auth_headers
                                    )
        assert response_post.status_code == 201
        created_tx_id = response_post.get_json()['id']

        response = client.put(f"/api/v1/categories/{created_tx_id}",
                                    json=test_data,
                                    headers=auth_headers
                                    )
        assert  response.status_code == expected_status
        json_data = response.get_json()
        assert expected_error_fragment in str(json_data)

    def test_update_category_wo_auth(self, client):
        response = client.put("/api/v1/categories/100")
        assert response.status_code == 401

    def test_update_category_perm_error(self, client, auth_headers):
        response = client.put("/api/v1/categories/100", headers=auth_headers, json={"name": "Check perm error"})
        assert  response.status_code == 404


class TestDeleteCategory:

    def test_delete_category_success(self, client, auth_headers):
        response_post = client.post("/api/v1/categories/",
                                    json=BASE_CREATE_CAT_JSON,
                                    headers=auth_headers
                                    )
        assert response_post.status_code == 201
        created_tx_id = response_post.get_json()['id']

        response = client.delete(f"/api/v1/categories/{created_tx_id}", headers=auth_headers)
        assert response.status_code == 204

    def test_delete_category_failed(self, client, auth_headers):
        response = client.delete("/api/v1/categories/100", headers=auth_headers)
        assert response.status_code == 404

    def test_delete_transaction_wo_auth(self, client):
        response = client.delete("/api/v1/categories/1")
        assert response.status_code == 401

class TestGetCategories:

    def test_get_all_categories_success(self, client, auth_headers):
        response = client.get("/api/v1/categories/all", headers=auth_headers)
        assert response.status_code == 200

    def test_get_all_categories_wo_auth(self, client):
        response = client.get("/api/v1/categories/all")
        assert response.status_code == 401


