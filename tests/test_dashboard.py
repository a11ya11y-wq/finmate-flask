import pytest

@pytest.mark.usefixtures("db_session")
class TestGetDashboard:

    def test_get_dashboard_success(self, client, auth_headers):
        client.post("/api/v1/transactions/",
                    headers=auth_headers,
                    json={
                        "amount":"1000",
                        "title": "TEST",
                        "transaction_type": "income",
                        "category_id": "1"
                    }
                    )
        client.post("/api/v1/transactions/",
                    headers=auth_headers,
                    json={
                        "amount":"250",
                        "title": "TEST2",
                        "transaction_type": "expense",
                        "category_id": "2"
                    }
                    )
        response = client.get("/api/v1/dashboard/", headers=auth_headers)
        assert response.status_code == 200

    def test_get_dashboard_stats_calculation(self, client, auth_headers):

        client.post("/api/v1/transactions/", headers=auth_headers, json={
            "amount": 1000,
            "title": "Salary",
            "transaction_type": "income",
            "category_id": 1
        })

        client.post("/api/v1/transactions/", headers=auth_headers, json={
            "amount": 250,
            "title": "Sushi",
            "transaction_type": "expense",
            "category_id": 2
        })

        response = client.get("/api/v1/dashboard/", headers=auth_headers)

        assert response.status_code == 200

        data = response.get_json()

        assert "stats" in data
        assert "charts" in data
        assert "recent_transactions" in data

        stats = data["stats"]

        assert float(stats["total_income"]) == 1000.00
        assert float(stats["total_expense"]) == 250.00
        assert float(stats["current_balance"]) == 750.00
        assert len(data["recent_transactions"]) == 2

    def test_get_dashboard_period_filter(self, client, auth_headers):
        response = client.get("/api/v1/dashboard/?period=week", headers=auth_headers)
        assert response.status_code == 200

        response = client.get("/api/v1/dashboard/?period=month", headers=auth_headers)
        assert response.status_code == 200


    def test_get_dashboard_wo_auth(self, client):
        response = client.get("/api/v1/dashboard/")
        assert response.status_code == 401


