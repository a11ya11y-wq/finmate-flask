from pydantic import ValidationError
import pytest
from unittest.mock import MagicMock
from freezegun import freeze_time
from datetime import datetime, timezone

from core_service.exceptions import BusinessLogicError, ResourceNotFound
from core_service.budgets.service import BudgetService


@pytest.fixture
def uow():    
    mock_uow = MagicMock()
    return mock_uow


BUDGET_DATA = {
    'id': 1,
    'category_id': 2,
    'amount': 100.0,
    'created_at': datetime(2024, 1, 1, tzinfo=timezone.utc)
}
class TestGetBudgets:

    @freeze_time("2024-01-15")
    @pytest.mark.parametrize("is_recurring, expected_deadline_info", [
        (True, '16 days left'),  # Recurring budget with 16 days left
        (False, 'Active for 14 days')  # One-time budget active for 14 days
    ])
    def test_get_all_budgets_with_stats(self, uow, is_recurring, expected_deadline_info):
        user_id = 1
        mock_budget = MagicMock()
        budget_dict = BUDGET_DATA.copy()
        budget_dict['is_recurring'] = is_recurring
        budget_dict['created_at'] = '2024-01-01T00:00:00Z'
        mock_budget.to_dict.return_value = budget_dict
        
        mock_budget.id = BUDGET_DATA['id']
        mock_budget.category_id = BUDGET_DATA['category_id']
        mock_budget.amount = BUDGET_DATA['amount']
        mock_budget.is_recurring = is_recurring

        mock_budget.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)

        uow.budget.get_all_budgets_by_user.return_value = [mock_budget]
        uow.budget.get_recurring_spent_map.return_value = {2: 70.0}
        uow.budget.get_one_time_spent_map.return_value = {2: 70.0}

        service = BudgetService(uow)
        result = service.get_all_budgets_with_stats(user_id)

        uow.budget.get_all_budgets_by_user.assert_called_once_with(user_id)
        uow.budget.get_recurring_spent_map.assert_called_once_with(user_id)
        uow.budget.get_one_time_spent_map.assert_called_once_with(user_id)
        
        expected_result = [{
            'id': 1,
            'category_id': 2,
            'amount': 100.0,
            'is_recurring': is_recurring,
            'created_at': '2024-01-01T00:00:00Z',
            'total_spent': 70.0,
            'deadline_info': expected_deadline_info,
            'percentage': 70.0,
            'remaining': 30.0
        }]
        assert result == expected_result

    def test_get_all_budgets_with_stats_no_budgets(self, uow):
        user_id = 1
        uow.budget.get_all_budgets_by_user.return_value = []
        uow.budget.get_recurring_spent_map.return_value = {}
        uow.budget.get_one_time_spent_map.return_value = {}

        service = BudgetService(uow)
        result = service.get_all_budgets_with_stats(user_id)

        uow.budget.get_all_budgets_by_user.assert_called_once_with(user_id)
        uow.budget.get_recurring_spent_map.assert_called_once_with(user_id)
        uow.budget.get_one_time_spent_map.assert_called_once_with(user_id)
        
        assert result == []

    @freeze_time("2024-01-15")
    def test_get_all_budgets_with_stats_zero_amount(self, uow):
        user_id = 1
        mock_budget = MagicMock()
        budget_dict = BUDGET_DATA.copy()
        budget_dict['amount'] = 0.0
        budget_dict['is_recurring'] = True
        budget_dict['created_at'] = '2024-01-01T00:00:00Z'
        mock_budget.to_dict.return_value = budget_dict
        
        mock_budget.id = BUDGET_DATA['id']
        mock_budget.category_id = BUDGET_DATA['category_id']
        mock_budget.amount = 0.0
        mock_budget.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)

        uow.budget.get_all_budgets_by_user.return_value = [mock_budget]
        uow.budget.get_recurring_spent_map.return_value = {2: 50.0}
        uow.budget.get_one_time_spent_map.return_value = {2: 50.0}

        service = BudgetService(uow)
        result = service.get_all_budgets_with_stats(user_id)

        uow.budget.get_all_budgets_by_user.assert_called_once_with(user_id)
        uow.budget.get_recurring_spent_map.assert_called_once_with(user_id)
        uow.budget.get_one_time_spent_map.assert_called_once_with(user_id)
        
        expected_result = [{
            'id': 1,
            'category_id': 2,
            'amount': 0.0,
            'is_recurring': True,
            'created_at': '2024-01-01T00:00:00Z',
            'total_spent': 50.0,
            'deadline_info': '16 days left',
            'percentage': 0.0,  # Should be 0% since amount is zero
            'remaining': -50.0  # Remaining can be negative if overspent
        }]
        assert result == expected_result

    @freeze_time("2024-01-15")
    def test_get_all_budgets_with_stats_no_spent(self, uow):
        user_id = 1
        mock_budget = MagicMock()
        budget_dict = BUDGET_DATA.copy()
        budget_dict['is_recurring'] = True
        budget_dict['created_at'] = '2024-01-01T00:00:00Z'
        mock_budget.to_dict.return_value = budget_dict
        
        mock_budget.id = BUDGET_DATA['id']
        mock_budget.category_id = BUDGET_DATA['category_id']
        mock_budget.amount = BUDGET_DATA['amount']
        mock_budget.is_recurring = True
        mock_budget.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)

        uow.budget.get_all_budgets_by_user.return_value = [mock_budget]
        uow.budget.get_recurring_spent_map.return_value = {2: 0.0}
        uow.budget.get_one_time_spent_map.return_value = {2: 0.0}

        service = BudgetService(uow)
        result = service.get_all_budgets_with_stats(user_id)

        uow.budget.get_all_budgets_by_user.assert_called_once_with(user_id)
        uow.budget.get_recurring_spent_map.assert_called_once_with(user_id)
        uow.budget.get_one_time_spent_map.assert_called_once_with(user_id)
        
        expected_result = [{
            'id': 1,
            'category_id': 2,
            'amount': 100.0,
            'is_recurring': True,
            'created_at': '2024-01-01T00:00:00Z',
            'total_spent': 0.0,
            'deadline_info': '16 days left',
            'percentage': 0.0,  # Should be 0% since nothing spent
            'remaining': 100.0
        }]
        assert result == expected_result

    @freeze_time("2024-01-15")
    def test_get_all_budgets_with_stats_multiple_budgets(self, uow):
        user_id = 1
        mock_budget1 = MagicMock()
        budget_dict1 = BUDGET_DATA.copy()
        budget_dict1['id'] = 1
        budget_dict1['category_id'] = 2
        budget_dict1['amount'] = 100.0
        budget_dict1['is_recurring'] = True
        budget_dict1['created_at'] = '2024-01-01T00:00:00Z'
        mock_budget1.to_dict.return_value = budget_dict1
        
        mock_budget2 = MagicMock()
        budget_dict2 = BUDGET_DATA.copy()
        budget_dict2['id'] = 2
        budget_dict2['category_id'] = 3
        budget_dict2['amount'] = 200.0
        budget_dict2['is_recurring'] = False
        budget_dict2['created_at'] = '2024-01-10T00:00:00Z'
        mock_budget2.to_dict.return_value = budget_dict2

        mock_budget1.id = 1
        mock_budget1.category_id = 2
        mock_budget1.amount = 100.0
        mock_budget1.is_recurring = True
        mock_budget1.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)

        mock_budget2.id = 2
        mock_budget2.category_id = 3
        mock_budget2.amount = 200.0
        mock_budget2.is_recurring = False
        mock_budget2.created_at = datetime(2024, 1, 10, tzinfo=timezone.utc)

        uow.budget.get_all_budgets_by_user.return_value = [mock_budget1, mock_budget2]
        uow.budget.get_recurring_spent_map.return_value = {2: 50.0}
        uow.budget.get_one_time_spent_map.return_value = {3: 150.0}

        service = BudgetService(uow)
        result = service.get_all_budgets_with_stats(user_id)

        uow.budget.get_all_budgets_by_user.assert_called_once_with(user_id)
        uow.budget.get_recurring_spent_map.assert_called_once_with(user_id)
        uow.budget.get_one_time_spent_map.assert_called_once_with(user_id)
        
        expected_result = [
            {
                'id': 2,
                'category_id': 3,
                'amount': 200.0,
                'is_recurring': False,
                'created_at': '2024-01-10T00:00:00Z',
                'total_spent': 150.0,
                'deadline_info': 'Active for 5 days',
                'percentage': 75.0,
                'remaining': 50.0
            },
            {
                'id': 1,
                'category_id': 2,
                'amount': 100.0,
                'is_recurring': True,
                'created_at': '2024-01-01T00:00:00Z',
                'total_spent': 50.0,
                'deadline_info': '16 days left',
                'percentage': 50.0,
                'remaining': 50.0
            },
        ]
        assert result == expected_result

VALID_BUDGET_DATA = {
    'category_id': 2,
    'amount': 100.0,
    'is_recurring': True,
}
class TestCreateBudget:
    @freeze_time("2024-01-15")
    def test_create_budget(self, uow):
        user_id = 1
        category = MagicMock()
        
        uow.categories.get_by_id_and_user.return_value = category
        uow.budget.get_by_category_and_user.return_value = None
        uow.budget.get_count_by_user.return_value = 1

        expected_result = VALID_BUDGET_DATA | {'user_id': user_id, 'created_at': '2024-01-15T00:00:00Z'}
        mock_new_budget = MagicMock()
        mock_new_budget.to_dict.return_value = expected_result

        uow.budget.create_budget.return_value = mock_new_budget

        service = BudgetService(uow)
        result, is_created = service.create_or_update_budget(user_id, VALID_BUDGET_DATA)

        uow.categories.get_cat_by_id_and_user.assert_called_once_with(2, user_id)
        uow.budget.get_by_category_and_user.assert_called_once_with(user_id, 2)
        uow.budget.create_budget.assert_called_once_with(VALID_BUDGET_DATA | {'user_id': user_id})
        uow.flush.assert_called_once()
        uow.on_commit.assert_called_once()

        assert result.to_dict() == expected_result
        assert is_created is True

    def test_create_budget_category_not_found(self, uow):
        user_id = 1
        
        uow.categories.get_cat_by_id_and_user.return_value = None

        service = BudgetService(uow)
        with pytest.raises(ResourceNotFound) as exc_info:
            service.create_or_update_budget(user_id, VALID_BUDGET_DATA)

        uow.categories.get_cat_by_id_and_user.assert_called_once_with(2, user_id)
        uow.budget.get_by_category_and_user.assert_not_called()
        uow.budget.create_budget.assert_not_called()
        assert "Category 2 not found or access denied." in str(exc_info.value)
        uow.flush.assert_not_called()
        uow.on_commit.assert_not_called()

    @freeze_time("2024-01-15")
    @pytest.mark.parametrize("invalid_data", [
        {'amount': -50.0},  # Negative amount
        {'is_recurring': 'not_a_boolean'},  # Invalid boolean
        {},  # Missing required fields
        {'amount': 'one hundred'},  # Invalid amount type
        {'category_id': 'two'},  # Invalid category_id type
        {'is_recurring': None},  # Invalid is_recurring type
        {'amount': 100.0, 'category_id': 2},  # Missing is_recurring
        {'amount': 100.0, 'is_recurring': True},  # Missing category_id
        {'category_id': 2, 'is_recurring': True}  # Missing amount
        ])
    def test_create_budget_validation(self, uow, invalid_data):
        user_id = 1
        category = MagicMock()
        
        uow.categories.get_cat_by_id_and_user.return_value = category

        service = BudgetService(uow)
        with pytest.raises(ValidationError):
            service.create_or_update_budget(user_id, invalid_data)

        uow.categories.get_cat_by_id_and_user.assert_not_called()
        uow.budget.get_by_category_and_user.assert_not_called()
        uow.budget.create_budget.assert_not_called()
        uow.flush.assert_not_called()
        uow.on_commit.assert_not_called()

    def test_create_budgets_over_limit(self, uow):
        user_id = 1
        category = MagicMock()
        
        uow.categories.get_cat_by_id_and_user.return_value = category
        uow.budget.get_by_category_and_user.return_value = None
        uow.budget.get_count_by_user.return_value = 5

        service = BudgetService(uow)
        with pytest.raises(BusinessLogicError) as exc_info:
            service.create_or_update_budget(user_id, VALID_BUDGET_DATA)

        uow.categories.get_cat_by_id_and_user.assert_called_once_with(2, user_id)
        uow.budget.get_by_category_and_user.assert_called_once_with(user_id, 2)
        uow.budget.create_budget.assert_not_called()
        assert "You have reached the limit of 5 budgets" in str(exc_info.value)
        uow.flush.assert_not_called()
        uow.on_commit.assert_not_called()

class TestUpdateBudget:

    @freeze_time("2024-01-16")
    def test_update_budget(self, uow):
        user_id = 1
        category_id = 2

        updated_data = {
            'amount': 150.0,
            "category_id": category_id,
            'is_recurring': False
        }
 
        existing_budget = MagicMock()
        existing_budget.category_id = category_id
   
        expected_payload = {
            "category_id": category_id, 
            'amount': 150.0, 
            'is_recurring': False, 
            'user_id': user_id, 
            'created_at': '2024-01-15T00:00:00Z'
        }
        existing_budget.to_dict.return_value = expected_payload

        uow.categories.get_cat_by_id_and_user.return_value = MagicMock()
        uow.budget.get_by_category_and_user.return_value = existing_budget
        uow.budget.update_budget.return_value = existing_budget

        service = BudgetService(uow)
        updated_budget, is_created = service.create_or_update_budget(user_id, updated_data)

        assert updated_budget.to_dict() == expected_payload
        assert is_created is False
        
        uow.categories.get_cat_by_id_and_user.assert_called_once_with(category_id, user_id)
        uow.budget.get_by_category_and_user.assert_called_once_with(user_id, category_id)
        
        uow.budget.update_budget.assert_called_once_with(existing_budget, updated_data)

        uow.flush.assert_called_once()
        uow.on_commit.assert_called_once()
    
    def test_update_budget_category_not_found(self, uow):
        user_id = 1
        category_id = 2

        updated_data = {
            'amount': 150.0,
            "category_id": category_id,
            'is_recurring': False
        }
        uow.categories.get_cat_by_id_and_user.return_value = None
        service = BudgetService(uow)
        with pytest.raises(ResourceNotFound) as exc_info:
            service.create_or_update_budget(user_id, updated_data)
        
        uow.categories.get_cat_by_id_and_user.assert_called_once_with(category_id, user_id)
        uow.budget.get_by_category_and_user.assert_not_called()
        assert "Category 2 not found or access denied." in str(exc_info.value)
        uow.budget.update_budget.assert_not_called()
        uow.flush.assert_not_called()
        uow.on_commit.assert_not_called()

class TestDeleteBudget:

    def test_delete_budget_success(self, uow):
        user_id = 1
        budget_id = 1

        budget_to_delete = MagicMock()
        uow.budget.get_by_id_and_user.return_value = budget_to_delete

        service = BudgetService(uow)
        result = service.delete_budget(user_id, budget_id)

        assert result is True
        uow.budget.get_by_id_and_user.assert_called_once_with(budget_id, user_id)
        uow.budget.delete_budget.assert_called_once_with(budget_to_delete)
        uow.on_commit.assert_called_once()

    def test_delete_budget_not_found(self, uow):
        user_id = 1
        budget_id = 999

        uow.budget.get_by_id_and_user.return_value = None

        service = BudgetService(uow)
        with pytest.raises(ResourceNotFound) as exc_info:
            service.delete_budget(user_id, budget_id)

        uow.budget.get_by_id_and_user.assert_called_once_with(budget_id, user_id)
        uow.budget.delete_budget.assert_not_called()
        assert "Budget 999 not found or access denied." in str(exc_info.value)
        uow.on_commit.assert_not_called()