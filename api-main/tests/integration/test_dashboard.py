import allure
import pytest


@allure.feature("Dashboard")
@allure.story("Retrieve Dashboard Data")
@pytest.mark.usefixtures("db_session")
class TestGetDashboard:

    @allure.title("Successfully retrieve default dashboard data")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_get_dashboard_success(self, client, auth_headers):
        with allure.step("Arrange: Create test transactions (income and expense)"):
            client.post(
                "/api/v1/transactions/",
                headers=auth_headers,
                json={
                    "amount": "1000",
                    "title": "TEST",
                    "transaction_type": "income",
                    "category_id": "1",
                },
            )
            client.post(
                "/api/v1/transactions/",
                headers=auth_headers,
                json={
                    "amount": "250",
                    "title": "TEST2",
                    "transaction_type": "expense",
                    "category_id": "2",
                },
            )

        with allure.step("Act: Send GET request to /api/v1/dashboard/"):
            response = client.get("/api/v1/dashboard/", headers=auth_headers)

        with allure.step("Assert: Verify 200 OK status"):
            assert response.status_code == 200

    @allure.title("Verify dashboard statistics calculation")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_dashboard_stats_calculation(self, client, auth_headers):
        with allure.step("Arrange: Create transactions for calculation"):
            client.post(
                "/api/v1/transactions/",
                headers=auth_headers,
                json={
                    "amount": 1000,
                    "title": "Salary",
                    "transaction_type": "income",
                    "category_id": 1,
                },
            )
            client.post(
                "/api/v1/transactions/",
                headers=auth_headers,
                json={
                    "amount": 250,
                    "title": "Sushi",
                    "transaction_type": "expense",
                    "category_id": 2,
                },
            )

        with allure.step("Act: Send GET request to fetch dashboard"):
            response = client.get("/api/v1/dashboard/", headers=auth_headers)

        with allure.step(
            "Assert: Verify response structure contains stats, charts, and recent tx"
        ):
            assert response.status_code == 200
            data = response.get_json()
            assert "stats" in data
            assert "charts" in data
            assert "recent_transactions" in data

        with allure.step("Assert: Verify math in calculated statistics"):
            stats = data["stats"]
            assert float(stats["current_income"]) == 1000.00
            assert float(stats["current_expense"]) == 250.00
            assert float(stats["income_percentage_change"]) == 100.0
            assert float(stats["expense_percentage_change"]) == 100.0
            assert float(stats["current_balance"]) == 750.00
            assert len(data["recent_transactions"]) == 2

    @allure.title("Verify dashboard chart generation structure")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_dashboard_charts(self, client, auth_headers):
        with allure.step("Arrange: Create test transactions"):
            client.post(
                "/api/v1/transactions/",
                headers=auth_headers,
                json={
                    "amount": 1000,
                    "title": "Salary",
                    "transaction_type": "income",
                    "category_id": 1,
                },
            )
            client.post(
                "/api/v1/transactions/",
                headers=auth_headers,
                json={
                    "amount": 250,
                    "title": "Sushi",
                    "transaction_type": "expense",
                    "category_id": 2,
                },
            )

        with allure.step("Act: Fetch dashboard charts payload"):
            response = client.get("/api/v1/dashboard/", headers=auth_headers)
            data = response.get_json()
            charts = data["charts"]

        with allure.step(
            "Assert: Verify expenses_by_category chart structure and values"
        ):
            assert "expenses_by_category" in charts
            assert "balance_dynamics" in charts

            cat_chart = charts["expenses_by_category"]
            assert "labels" in cat_chart
            assert "data" in cat_chart
            assert len(cat_chart["labels"]) == len(cat_chart["data"])
            assert 250.0 in cat_chart["data"]

        with allure.step(
            "Assert: Verify balance_dynamics chart structure and chronological math"
        ):
            bal_chart = charts["balance_dynamics"]
            assert len(bal_chart["labels"]) == len(bal_chart["data"])
            assert len(bal_chart["labels"]) == 2
            assert bal_chart["data"][0] == 1000.0
            assert bal_chart["data"][1] == 750.0

    @allure.title("Retrieve dashboard data with specific period filters")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_dashboard_period_filter(self, client, auth_headers):
        with allure.step("Act & Assert: Fetch and verify for 'week' period"):
            response = client.get(
                "/api/v1/dashboard/?period=week", headers=auth_headers
            )
            assert response.status_code == 200

        with allure.step("Act & Assert: Fetch and verify for 'month' period"):
            response = client.get(
                "/api/v1/dashboard/?period=month", headers=auth_headers
            )
            assert response.status_code == 200

    @allure.title("Fail to retrieve dashboard without authorization")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_dashboard_wo_auth(self, client):
        with allure.step("Act: Send GET request without auth headers"):
            response = client.get("/api/v1/dashboard/")

        with allure.step("Assert: Verify 401 Unauthorized"):
            assert response.status_code == 401
