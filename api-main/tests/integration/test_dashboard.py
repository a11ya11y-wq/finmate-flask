import pytest


@pytest.mark.usefixtures("db_session")
class TestGetDashboard:

    def test_get_dashboard_success(self, client, auth_headers):
        client.post("/api/v1/transactions/",
                    headers=auth_headers,
                    json={
                        "amount": "1000",
                        "title": "TEST",
                        "transaction_type": "income",
                        "category_id": "1"
                    }
                    )
        client.post("/api/v1/transactions/",
                    headers=auth_headers,
                    json={
                        "amount": "250",
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

        assert float(stats["current_income"]) == 1000.00
        assert float(stats["current_expense"]) == 250.00

        assert float(stats["income_percentage_change"]) == 100.0
        assert float(stats["expense_percentage_change"]) == 100.0

        assert float(stats["current_balance"]) == 750.00
        assert len(data["recent_transactions"]) == 2

    def test_get_dashboard_charts(self, client, auth_headers):
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
        data = response.get_json()

        charts = data["charts"]

        assert "expenses_by_category" in charts
        assert "balance_dynamics" in charts

        cat_chart = charts["expenses_by_category"]
        assert "labels" in cat_chart
        assert "data" in cat_chart
        assert len(cat_chart["labels"]) == len(cat_chart["data"])

        assert 250.0 in cat_chart["data"]

        bal_chart = charts["balance_dynamics"]
        assert len(bal_chart["labels"]) == len(bal_chart["data"])

        assert len(bal_chart["labels"]) == 2

        assert bal_chart["data"][0] == 1000.0

        assert bal_chart["data"][1] == 750.0

    def test_get_dashboard_period_filter(self, client, auth_headers):
        response = client.get("/api/v1/dashboard/?period=week", headers=auth_headers)
        assert response.status_code == 200

        response = client.get("/api/v1/dashboard/?period=month", headers=auth_headers)
        assert response.status_code == 200

    def test_get_dashboard_wo_auth(self, client):
        response = client.get("/api/v1/dashboard/")
        assert response.status_code == 401
