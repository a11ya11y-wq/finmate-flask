from datetime import datetime, timezone
from unittest.mock import MagicMock

import allure
import pytest
from core_service.budgets.service import BudgetService
from core_service.exceptions import BusinessLogicError, ResourceNotFound
from freezegun import freeze_time
from pydantic import ValidationError


@pytest.fixture
@allure.title("Initialize Mocked Budget UOW")
def uow():
    with allure.step("Initialize MagicMock for Budget Unit of Work"):
        return MagicMock()


BUDGET_DATA = {
    "id": 1,
    "category_id": 2,
    "amount": 100.0,
    "created_at": datetime(2024, 1, 1, tzinfo=timezone.utc),
}


@allure.feature("Budget Management")
@allure.story("Retrieve Budgets")
class TestGetBudgets:

    @allure.title(
        "Retrieve all budgets with valid statistics (is_recurring={is_recurring})"
    )
    @allure.severity(allure.severity_level.BLOCKER)
    @freeze_time("2024-01-15")
    @pytest.mark.parametrize(
        "is_recurring, expected_deadline_info",
        [(True, "16 days left"), (False, "Active for 14 days")],
    )
    def test_get_all_budgets_with_stats(
        self, uow, is_recurring, expected_deadline_info
    ):
        with allure.step("Arrange: Mock budget data and spending maps"):
            user_id = 1
            mock_budget = MagicMock()
            budget_dict = BUDGET_DATA.copy()
            budget_dict["is_recurring"] = is_recurring
            budget_dict["created_at"] = "2024-01-01T00:00:00Z"
            mock_budget.to_dict.return_value = budget_dict

            mock_budget.id = BUDGET_DATA["id"]
            mock_budget.category_id = BUDGET_DATA["category_id"]
            mock_budget.amount = BUDGET_DATA["amount"]
            mock_budget.is_recurring = is_recurring
            mock_budget.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)

            uow.budget.get_all_budgets_by_user.return_value = [mock_budget]
            uow.budget.get_recurring_spent_map.return_value = {2: 70.0}
            uow.budget.get_one_time_spent_map.return_value = {2: 70.0}

        with allure.step("Act: Call get_all_budgets_with_stats"):
            service = BudgetService(uow)
            result = service.get_all_budgets_with_stats(user_id)

        with allure.step("Assert: Verify UOW calls and stats calculations"):
            uow.budget.get_all_budgets_by_user.assert_called_once_with(user_id)
            uow.budget.get_recurring_spent_map.assert_called_once_with(user_id)
            uow.budget.get_one_time_spent_map.assert_called_once_with(user_id)

            expected_result = [
                {
                    "id": 1,
                    "category_id": 2,
                    "amount": 100.0,
                    "is_recurring": is_recurring,
                    "created_at": "2024-01-01T00:00:00Z",
                    "total_spent": 70.0,
                    "deadline_info": expected_deadline_info,
                    "percentage": 70.0,
                    "remaining": 30.0,
                }
            ]
            assert result == expected_result

    @allure.title("Retrieve stats when user has no active budgets")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_all_budgets_with_stats_no_budgets(self, uow):
        with allure.step("Arrange: Mock empty returns from UOW"):
            user_id = 1
            uow.budget.get_all_budgets_by_user.return_value = []
            uow.budget.get_recurring_spent_map.return_value = {}
            uow.budget.get_one_time_spent_map.return_value = {}

        with allure.step("Act: Fetch budgets"):
            service = BudgetService(uow)
            result = service.get_all_budgets_with_stats(user_id)

        with allure.step("Assert: Verify empty list is returned"):
            assert result == []

    @allure.title("Retrieve stats for a budget with zero total amount")
    @allure.severity(allure.severity_level.NORMAL)
    @freeze_time("2024-01-15")
    def test_get_all_budgets_with_stats_zero_amount(self, uow):
        with allure.step("Arrange: Mock budget with zero limit but active spending"):
            user_id = 1
            mock_budget = MagicMock()
            budget_dict = BUDGET_DATA.copy()
            budget_dict["amount"] = 0.0
            budget_dict["is_recurring"] = True
            budget_dict["created_at"] = "2024-01-01T00:00:00Z"
            mock_budget.to_dict.return_value = budget_dict

            mock_budget.id = BUDGET_DATA["id"]
            mock_budget.category_id = BUDGET_DATA["category_id"]
            mock_budget.amount = 0.0
            mock_budget.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)

            uow.budget.get_all_budgets_by_user.return_value = [mock_budget]
            uow.budget.get_recurring_spent_map.return_value = {2: 50.0}
            uow.budget.get_one_time_spent_map.return_value = {2: 50.0}

        with allure.step("Act: Fetch budgets"):
            service = BudgetService(uow)
            result = service.get_all_budgets_with_stats(user_id)

        with allure.step("Assert: Ensure percentage is 0 and remaining is negative"):
            expected_result = [
                {
                    "id": 1,
                    "category_id": 2,
                    "amount": 0.0,
                    "is_recurring": True,
                    "created_at": "2024-01-01T00:00:00Z",
                    "total_spent": 50.0,
                    "deadline_info": "16 days left",
                    "percentage": 0.0,
                    "remaining": -50.0,
                }
            ]
            assert result == expected_result

    @allure.title("Retrieve stats for a budget with zero spent amount")
    @allure.severity(allure.severity_level.NORMAL)
    @freeze_time("2024-01-15")
    def test_get_all_budgets_with_stats_no_spent(self, uow):
        with allure.step("Arrange: Mock budget with zero active spending"):
            user_id = 1
            mock_budget = MagicMock()
            budget_dict = BUDGET_DATA.copy()
            budget_dict["is_recurring"] = True
            budget_dict["created_at"] = "2024-01-01T00:00:00Z"
            mock_budget.to_dict.return_value = budget_dict

            mock_budget.id = BUDGET_DATA["id"]
            mock_budget.category_id = BUDGET_DATA["category_id"]
            mock_budget.amount = BUDGET_DATA["amount"]
            mock_budget.is_recurring = True
            mock_budget.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)

            uow.budget.get_all_budgets_by_user.return_value = [mock_budget]
            uow.budget.get_recurring_spent_map.return_value = {2: 0.0}
            uow.budget.get_one_time_spent_map.return_value = {2: 0.0}

        with allure.step("Act: Fetch budgets"):
            service = BudgetService(uow)
            result = service.get_all_budgets_with_stats(user_id)

        with allure.step("Assert: Ensure remaining equals total amount"):
            assert result[0]["percentage"] == 0.0
            assert result[0]["remaining"] == 100.0

    @allure.title("Retrieve stats when multiple budgets exist")
    @allure.severity(allure.severity_level.CRITICAL)
    @freeze_time("2024-01-15")
    def test_get_all_budgets_with_stats_multiple_budgets(self, uow):
        with allure.step("Arrange: Mock multiple budgets (recurring and one-time)"):
            user_id = 1
            mock_budget1 = MagicMock(
                id=1, category_id=2, amount=100.0, is_recurring=True
            )
            mock_budget1.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
            mock_budget1.to_dict.return_value = BUDGET_DATA.copy() | {
                "id": 1,
                "category_id": 2,
                "amount": 100.0,
                "is_recurring": True,
                "created_at": "2024-01-01T00:00:00Z",
            }

            mock_budget2 = MagicMock(
                id=2, category_id=3, amount=200.0, is_recurring=False
            )
            mock_budget2.created_at = datetime(2024, 1, 10, tzinfo=timezone.utc)
            mock_budget2.to_dict.return_value = BUDGET_DATA.copy() | {
                "id": 2,
                "category_id": 3,
                "amount": 200.0,
                "is_recurring": False,
                "created_at": "2024-01-10T00:00:00Z",
            }

            uow.budget.get_all_budgets_by_user.return_value = [
                mock_budget1,
                mock_budget2,
            ]
            uow.budget.get_recurring_spent_map.return_value = {2: 50.0}
            uow.budget.get_one_time_spent_map.return_value = {3: 150.0}

        with allure.step("Act: Fetch budgets"):
            service = BudgetService(uow)
            result = service.get_all_budgets_with_stats(user_id)

        with allure.step("Assert: Verify response lists both budgets correctly"):
            assert len(result) == 2


VALID_BUDGET_DATA = {
    "category_id": 2,
    "amount": 100.0,
    "is_recurring": True,
}


@allure.feature("Budget Management")
@allure.story("Create Budget")
class TestCreateBudget:

    @allure.title("Successfully create a new budget")
    @allure.severity(allure.severity_level.BLOCKER)
    @freeze_time("2024-01-15")
    def test_create_budget(self, uow):
        with allure.step("Arrange: Mock dependencies and limits"):
            user_id = 1
            uow.categories.get_by_id_and_user.return_value = MagicMock()
            uow.budget.get_by_category_and_user.return_value = None
            uow.budget.get_count_by_user.return_value = 1

            expected_result = VALID_BUDGET_DATA | {
                "user_id": user_id,
                "created_at": "2024-01-15T00:00:00Z",
            }
            mock_new_budget = MagicMock()
            mock_new_budget.to_dict.return_value = expected_result
            uow.budget.create_budget.return_value = mock_new_budget

        with allure.step("Act: Call create_or_update_budget"):
            service = BudgetService(uow)
            result, is_created = service.create_or_update_budget(
                user_id, VALID_BUDGET_DATA
            )

        with allure.step("Assert: Validate response and UOW commit"):
            uow.budget.create_budget.assert_called_once_with(
                VALID_BUDGET_DATA | {"user_id": user_id}
            )
            uow.flush.assert_called_once()
            uow.on_commit.assert_called_once()
            assert result.to_dict() == expected_result
            assert is_created is True

    @allure.title("Fail to create a budget if category is not found")
    @allure.severity(allure.severity_level.NORMAL)
    def test_create_budget_category_not_found(self, uow):
        with allure.step("Arrange: Mock category missing"):
            user_id = 1
            uow.categories.get_cat_by_id_and_user.return_value = None

        with allure.step("Act & Assert: Expect ResourceNotFound"):
            service = BudgetService(uow)
            with pytest.raises(
                ResourceNotFound, match="Category 2 not found or access denied."
            ):
                service.create_or_update_budget(user_id, VALID_BUDGET_DATA)

        with allure.step("Assert: Validate commit was not called"):
            uow.budget.create_budget.assert_not_called()
            uow.flush.assert_not_called()

    @allure.title("Validation errors on invalid payload during creation")
    @allure.severity(allure.severity_level.CRITICAL)
    @freeze_time("2024-01-15")
    @pytest.mark.parametrize(
        "invalid_data",
        [
            {"amount": -50.0},
            {"is_recurring": "not_a_boolean"},
            {},
            {"amount": "one hundred"},
            {"category_id": "two"},
            {"is_recurring": None},
            {"amount": 100.0, "category_id": 2},
            {"amount": 100.0, "is_recurring": True},
            {"category_id": 2, "is_recurring": True},
        ],
    )
    def test_create_budget_validation(self, uow, invalid_data):
        with allure.step("Arrange: Mock existing category"):
            user_id = 1
            uow.categories.get_cat_by_id_and_user.return_value = MagicMock()

        with allure.step("Act & Assert: Expect ValidationError"):
            service = BudgetService(uow)
            with pytest.raises(ValidationError):
                service.create_or_update_budget(user_id, invalid_data)

    @allure.title("Fail to create budget if user reached limit")
    @allure.severity(allure.severity_level.NORMAL)
    def test_create_budgets_over_limit(self, uow):
        with allure.step("Arrange: Mock limit reached"):
            user_id = 1
            uow.categories.get_cat_by_id_and_user.return_value = MagicMock()
            uow.budget.get_by_category_and_user.return_value = None
            uow.budget.get_count_by_user.return_value = 5

        with allure.step("Act & Assert: Expect BusinessLogicError"):
            service = BudgetService(uow)
            with pytest.raises(
                BusinessLogicError, match="You have reached the limit of 5 budgets"
            ):
                service.create_or_update_budget(user_id, VALID_BUDGET_DATA)


@allure.feature("Budget Management")
@allure.story("Update Budget")
class TestUpdateBudget:

    @allure.title("Successfully update an existing budget")
    @allure.severity(allure.severity_level.CRITICAL)
    @freeze_time("2024-01-16")
    def test_update_budget(self, uow):
        with allure.step("Arrange: Mock existing budget and update payload"):
            user_id = 1
            category_id = 2
            updated_data = {
                "amount": 150.0,
                "category_id": category_id,
                "is_recurring": False,
            }

            existing_budget = MagicMock()
            existing_budget.category_id = category_id
            expected_payload = {
                "category_id": category_id,
                "amount": 150.0,
                "is_recurring": False,
                "user_id": user_id,
                "created_at": "2024-01-15T00:00:00Z",
            }
            existing_budget.to_dict.return_value = expected_payload

            uow.categories.get_cat_by_id_and_user.return_value = MagicMock()
            uow.budget.get_by_category_and_user.return_value = existing_budget
            uow.budget.update_budget.return_value = existing_budget

        with allure.step("Act: Call create_or_update_budget"):
            service = BudgetService(uow)
            updated_budget, is_created = service.create_or_update_budget(
                user_id, updated_data
            )

        with allure.step("Assert: Validate updated response and UOW calls"):
            assert updated_budget.to_dict() == expected_payload
            assert is_created is False
            uow.budget.update_budget.assert_called_once_with(
                existing_budget, updated_data
            )
            uow.flush.assert_called_once()
            uow.on_commit.assert_called_once()

    @allure.title("Fail to update budget if category is not found")
    @allure.severity(allure.severity_level.NORMAL)
    def test_update_budget_category_not_found(self, uow):
        with allure.step("Arrange: Mock category missing"):
            user_id = 1
            category_id = 2
            updated_data = {
                "amount": 150.0,
                "category_id": category_id,
                "is_recurring": False,
            }
            uow.categories.get_cat_by_id_and_user.return_value = None

        with allure.step("Act & Assert: Expect ResourceNotFound"):
            service = BudgetService(uow)
            with pytest.raises(
                ResourceNotFound, match="Category 2 not found or access denied."
            ):
                service.create_or_update_budget(user_id, updated_data)


@allure.feature("Budget Management")
@allure.story("Delete Budget")
class TestDeleteBudget:

    @allure.title("Successfully delete an existing budget")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_budget_success(self, uow):
        with allure.step("Arrange: Mock budget exists"):
            user_id = 1
            budget_id = 1
            budget_to_delete = MagicMock()
            uow.budget.get_by_id_and_user.return_value = budget_to_delete

        with allure.step("Act: Call delete_budget"):
            service = BudgetService(uow)
            result = service.delete_budget(user_id, budget_id)

        with allure.step("Assert: Verify deletion call"):
            assert result is True
            uow.budget.delete_budget.assert_called_once_with(budget_to_delete)
            uow.on_commit.assert_called_once()

    @allure.title("Fail to delete non-existent budget")
    @allure.severity(allure.severity_level.NORMAL)
    def test_delete_budget_not_found(self, uow):
        with allure.step("Arrange: Mock budget missing"):
            user_id = 1
            budget_id = 999
            uow.budget.get_by_id_and_user.return_value = None

        with allure.step("Act & Assert: Expect ResourceNotFound"):
            service = BudgetService(uow)
            with pytest.raises(
                ResourceNotFound, match="Budget 999 not found or access denied."
            ):
                service.delete_budget(user_id, budget_id)
