import math
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock

import allure
import pytest
from core_service.dashboard.service import DashboardService
from core_service.exceptions import BusinessLogicError
from core_service.models.user_model import Users


@pytest.fixture
@allure.title("Initialize Mocked Dashboard UOW")
def dashboard_uow():
    with allure.step("Setup basic mock returns for profile and transactions"):
        mock_uow = MagicMock()

        mock_user = MagicMock(spec=Users)
        mock_user.id = 1
        mock_user.initial_balance = Decimal("1000.00")
        mock_uow.profile.get_user_info.return_value = mock_user

        mock_uow.transactions.get_total_amount.return_value = Decimal("500.00")
        mock_uow.transactions.get_current_balance.return_value = Decimal("1500.00")
        mock_uow.transactions.get_expense_by_category.return_value = [
            ("Food", Decimal("300.00")),
            (None, Decimal("200.00")),
        ]
        mock_uow.transactions.get_opening_balance.return_value = Decimal("1000.00")
        mock_uow.transactions.get_total_count_of_tx.return_value = 25

        return mock_uow


@allure.feature("Dashboard")
@allure.story("Data Aggregation")
class TestDashboardService:

    @allure.title("Successful retrieval of dashboard data for a valid period")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_get_dashboard_data_success(self, dashboard_uow):
        with allure.step("Arrange: Initialize service and mock recent transactions"):
            service = DashboardService(dashboard_uow)
            dashboard_uow.transactions.get_recent_transactions.return_value = []
            dashboard_uow.transactions.get_transactions_for_balance_chart.return_value = (
                []
            )

        with allure.step("Act: Fetch dashboard data for a week"):
            result = service.get_dashboard_data(user_id=1, period="week")

        with allure.step("Assert: Verify response structure and UOW calls"):
            assert "stats" in result
            assert "charts" in result
            assert "recent_transactions" in result
            dashboard_uow.profile.get_user_info.assert_called_once_with(1)

    @allure.title("Fails when period is invalid")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_dashboard_data_invalid_period(self, dashboard_uow):
        with allure.step("Arrange: Initialize service"):
            service = DashboardService(dashboard_uow)

        with allure.step("Act & Assert: Expect BusinessLogicError for 'year' period"):
            with pytest.raises(BusinessLogicError, match="Invalid period 'year'"):
                service.get_dashboard_data(user_id=1, period="year")

        with allure.step("Assert: Ensure user info was not requested"):
            dashboard_uow.profile.get_user_info.assert_not_called()

    @allure.title("Check offset calculation for transaction history pagination")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_tx_history_pagination(self, dashboard_uow):
        with allure.step("Arrange: Mock transaction list"):
            service = DashboardService(dashboard_uow)
            mock_tx = MagicMock()
            mock_tx.to_dict.return_value = {"id": 1, "amount": 100}
            dashboard_uow.transactions.get_recent_transactions.return_value = [
                mock_tx,
                mock_tx,
            ]

        with allure.step("Act: Fetch transaction history for page 2"):
            result = service.get_tx_history(user_id=1, period="month", page=2)

        with allure.step("Assert: Verify offset math and limit"):
            args, kwargs = dashboard_uow.transactions.get_recent_transactions.call_args
            assert kwargs["limit"] == 15
            assert kwargs["offset"] == 15
            assert len(result["data"]) == 2

    @allure.title("Check math for stats calculations (balances and percentages)")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_stats_calculations(self, dashboard_uow):
        with allure.step("Arrange: Set up mock transaction amounts"):
            service = DashboardService(dashboard_uow)
            mock_user = dashboard_uow.profile.get_user_info(1)
            start_date = datetime.now()

            dashboard_uow.transactions.get_total_amount.side_effect = [
                Decimal("500.0"),  # current_income
                Decimal("500.0"),  # current_expense
                Decimal("500.0"),  # prev_income
                Decimal("250.0"),  # prev_expense
            ]

        with allure.step("Act: Calculate stats"):
            stats = service._get_stats(mock_user, "month", start_date)

        with allure.step("Assert: Validate balance sum and percentage changes"):
            assert stats["current_balance"] == 2500.0
            assert stats["income_percentage_change"] == 0.0
            assert stats["expense_percentage_change"] == 100.0

    @allure.title("Handle None categories and None amounts in category charts")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_category_chart_none_handling(self, dashboard_uow):
        with allure.step("Arrange: Mock categories with None values"):
            service = DashboardService(dashboard_uow)
            mock_user = dashboard_uow.profile.get_user_info(1)

            dashboard_uow.transactions.get_expense_by_category.return_value = [
                ("Transport", Decimal("150.50")),
                (None, Decimal("50.00")),
                ("Gifts", None),
            ]

        with allure.step("Act: Generate category chart data"):
            chart_data = service._get_category_chart(mock_user, datetime.now())

        with allure.step("Assert: Verify labels and parsed data"):
            assert chart_data["labels"] == ["Transport", "Uncategorized", "Gifts"]
            assert chart_data["data"] == [150.5, 50.0, 0.0]

    @allure.title("Calculate balance dynamics for 'all' period")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_balance_dynamics_all_period(self, dashboard_uow):
        with allure.step("Arrange: Mock transactions for chart"):
            service = DashboardService(dashboard_uow)
            mock_user = dashboard_uow.profile.get_user_info(1)
            mock_user.initial_balance = Decimal("100.00")

            tx1 = MagicMock(
                amount=Decimal("50.00"),
                transaction_type="income",
                created_at=datetime(2026, 5, 28),
            )
            tx2 = MagicMock(
                amount=Decimal("20.00"),
                transaction_type="expense",
                created_at=datetime(2026, 5, 29),
            )
            dashboard_uow.transactions.get_transactions_for_balance_chart.return_value = [
                tx1,
                tx2,
            ]

        with allure.step("Act: Get balance dynamics"):
            result = service._get_balance_dynamics(mock_user, "all", datetime.now())

        with allure.step(
            "Assert: Ensure opening balance is not fetched and verify labels/data"
        ):
            dashboard_uow.transactions.get_opening_balance.assert_not_called()
            assert result["labels"] == ["2026-05-28 00:00:00", "2026-05-29 00:00:00"]
            assert result["data"] == [150.0, 130.0]

    @allure.title("Check pagination ceiling math")
    @allure.severity(allure.severity_level.MINOR)
    def test_get_total_count_of_page(self, dashboard_uow):
        with allure.step("Arrange: Mock total transaction count to 31"):
            service = DashboardService(dashboard_uow)
            mock_user = dashboard_uow.profile.get_user_info(1)
            dashboard_uow.transactions.get_total_count_of_tx.return_value = 31

        with allure.step("Act: Calculate total pages"):
            total_pages = service._get_total_count_of_page(mock_user, datetime.now())

        with allure.step("Assert: Verify ceiling logic"):
            assert total_pages == 3


@allure.feature("Dashboard")
@allure.story("Static Calculation Utilities")
class TestDashboardStaticMethods:

    @allure.title(
        "Calculate percentage change (current={current}, previous={previous})"
    )
    @allure.severity(allure.severity_level.MINOR)
    @pytest.mark.parametrize(
        "current, previous, expected",
        [
            (150, 100, 50.0),
            (50, 100, -50.0),
            (100, 100, 0.0),
            (100, 0, 100.0),
            (0, 0, 0.0),
            (0, 100, -100.0),
            (33.333, 10, 233.3),
        ],
    )
    def test_calculate_percentage_change(self, current, previous, expected):
        with allure.step("Assert calculated percentage change matches expected"):
            assert (
                DashboardService._calculate_percentage_change(current, previous)
                == expected
            )

    @allure.title("Calculate previous period start date (period={period})")
    @allure.severity(allure.severity_level.MINOR)
    @pytest.mark.parametrize(
        "period, expected_days_delta",
        [
            ("week", 7),
            ("month", 30),
        ],
    )
    def test_calculate_prev_start_date(self, period, expected_days_delta):
        with allure.step("Arrange: Set static start date"):
            start_date = datetime(2026, 5, 20)
            expected_date = start_date - timedelta(days=expected_days_delta)

        with allure.step("Act & Assert: Validate calculated date"):
            assert (
                DashboardService._calculate_prev_start_date(period, start_date)
                == expected_date
            )
