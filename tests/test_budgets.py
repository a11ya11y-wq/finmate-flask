import pytest


BASE_BUDGET_JSON = {
    "amount": "1000",
    "category_id": 1,
    "is_recurring": True
}

create_bud_failed_json = [
    # Negative amount (Validation)
    (
        BASE_BUDGET_JSON | {"amount": -100},
        422,
        "Input should be greater than 0"
    ),
    # Incorrect tx_type (Validation)
    (
        BASE_BUDGET_JSON | {"is_recurring": "ANOTHER TYPE"},
        422,
        "Input should be a valid boolean, unable to interpret input"
    ),
    # Incorrect cat_id -> str (Validation)
    (
        BASE_BUDGET_JSON | {"category_id": "INCORRECT CAT_ID"},
        422,
        "Input should be a valid integer"
    ),
    # Not valid cat_id (Service)
    (
        BASE_BUDGET_JSON | {"category_id": 100},
        404,
        "Category 100 not found or access denied."
    ),
    # Not valid amount (Validation)
    (
        BASE_BUDGET_JSON | {"amount": "NOT VALID AMOUNT"},
        422,
        "Input should be a valid decimal"
    ),
    (
        {}, 422, "Field required"
    )
]

class TestCreateBudgets:

    def test_create_budgets_success(self, client, auth_headers):
        response = client.post("/api/v1/budgets/",
                               headers=auth_headers,
                               json=BASE_BUDGET_JSON
                               )
        assert response.status_code == 201


    @pytest.mark.parametrize(
        "test_data, expected_status, expected_error_fragment",
        create_bud_failed_json
    )
    def test_create_budgets_failed(self, client, auth_headers, test_data, expected_status, expected_error_fragment):
        response = client.post("/api/v1/budgets/",
                               headers=auth_headers,
                               json=test_data
                               )
        assert response.status_code == expected_status
        json_data = response.get_json()
        assert expected_error_fragment in str(json_data)

    def test_create_budgets_wo_auth(self, client):
        response = client.post("/api/v1/budgets/",
                               json=BASE_BUDGET_JSON
                               )
        assert response.status_code == 401

    def test_create_budgets_overlimit(self, client, auth_headers):
        response = client.get("/api/v1/categories/all", headers=auth_headers)
        assert response.status_code == 200
        response_json = response.json
        existing_categories = response_json['data']

        assert len(existing_categories) >= 6

        for i in range(5):
            cat_id = existing_categories[i]['id']
            response = client.post("/api/v1/budgets/", headers=auth_headers,
                                   json={
                                       "amount": "1000",
                                       "category_id": cat_id,
                                       "is_recurring": True
                                   }
                                   )
            assert response.status_code == 201

        extra_cat_id = existing_categories[5]['id']

        last_response = client.post("/api/v1/budgets/",
                                    headers=auth_headers,
                                    json={
                                        "amount": 100,
                                        "category_id": extra_cat_id,
                                        "is_recurring": True
                                    }
                                    )
        assert last_response.status_code == 400
        assert "limit" in str(last_response.get_json())

BASE_UPDATE_JSON = {
    "amount": "500",
    "category_id": 1,
    "is_recurring": False
}

update_bud_failed =[
    # Negative amount (Validation)
    (
        BASE_UPDATE_JSON | {"amount": -100},
        422,
        "Input should be greater than 0"
    ),
    # Incorrect tx_type (Validation)
    (
        BASE_UPDATE_JSON | {"is_recurring": "ANOTHER TYPE"},
        422,
        "Input should be a valid boolean, unable to interpret input"
    ),
    # Incorrect cat_id -> str (Validation)
    (
        BASE_UPDATE_JSON | {"category_id": "INCORRECT CAT_ID"},
        422,
        "Input should be a valid integer"
    ),
    # Not valid cat_id (Service)
    (
        BASE_UPDATE_JSON | {"category_id": 100},
        404,
        "Category 100 not found or access denied."
    ),
    # Not valid amount (Validation)
    (
        BASE_UPDATE_JSON | {"amount": "NOT VALID AMOUNT"},
        422,
        "Input should be a valid decimal"
    ),
    (
        {}, 422, "Field required"
    )
]

class TestUpdateBudgets:

    def test_update_budgets_success(self, client, auth_headers):
        response_post = client.post("/api/v1/budgets/",
                               headers=auth_headers,
                               json=BASE_BUDGET_JSON
                               )
        assert response_post.status_code == 201

        response = client.post("/api/v1/budgets/",
                               headers=auth_headers,
                               json=BASE_UPDATE_JSON
                               )
        assert response.status_code == 201


    @pytest.mark.parametrize(
        "test_data, expected_status, expected_error_fragment",
        update_bud_failed
    )
    def test_update_budgets_failed(self, client, auth_headers, test_data, expected_status, expected_error_fragment):
        response_post = client.post("/api/v1/budgets/",
                                    headers=auth_headers,
                                    json=BASE_BUDGET_JSON
                                    )
        assert response_post.status_code == 201

        response = client.post("/api/v1/budgets/",
                                    headers=auth_headers,
                                    json=test_data
                                    )
        assert response.status_code == expected_status
        json_data = response.get_json()
        assert expected_error_fragment in str(json_data)

    def test_update_budgets_wo_auth(self, client, auth_headers):
        response = client.post("/api/v1/budgets/",
                                    json=BASE_UPDATE_JSON
                                    )
        assert response.status_code == 401


class TestDeleteBudgets:

    def test_delete_budgets_success(self, client, auth_headers):
        response_post = client.post("/api/v1/budgets/",
                                    headers=auth_headers,
                                    json=BASE_BUDGET_JSON
                                    )
        created_bud_id = response_post.get_json()['id']

        response = client.delete(f'/api/v1/budgets/{created_bud_id}', headers = auth_headers)
        assert response.status_code == 204


    def test_delete_budgets_failed(self, client, auth_headers):
        response = client.delete("/api/v1/budgets/100",
                                    headers=auth_headers
                                    )
        assert  response.status_code == 404

    def test_delete_budgets_wo_auth(self,client):
        response = client.delete("/api/v1/budgets/100")
        assert response.status_code == 401



class TestGetBudgets:

    def test_get_all_budgets_success(self, client, auth_headers):
        client.post("/api/v1/budgets/",
                    headers=auth_headers,
                    json=BASE_BUDGET_JSON
                    )
        client.post("/api/v1/transactions/", headers=auth_headers, json={
            "amount": 250,
            "title": "Groceries",
            "transaction_type": "expense",
            "category_id": 1
        })
        client.post("/api/v1/transactions/", headers=auth_headers, json={
            "amount": 250,
            "title": "More Food",
            "transaction_type": "expense",
            "category_id": 1
        })
        response = client.get("/api/v1/budgets/", headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()

        assert len(data) == 1
        budget_stat = data[0]

        assert budget_stat['total_spent'] == 500.0
        assert budget_stat['remaining'] == 500.0
        assert budget_stat['percentage'] == 50.0

        assert "day" in budget_stat['deadline_info']
        assert "left" in budget_stat['deadline_info']

    def test_get_all_budgets_wo_auth(self, client):
        response = client.get("/api/v1/budgets/")
        assert response.status_code == 401

    #TODO: Додати перевірку ізоляції данних