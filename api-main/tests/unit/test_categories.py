import pytest
from unittest.mock import MagicMock
from pydantic import ValidationError

from core_service.categories.service import CategoryService
from core_service.exceptions import BusinessLogicError, ConflictError, ResourceNotFound

@pytest.fixture
def category_uow():
    mock_uow = MagicMock()
    return mock_uow


class TestGetCategories:

    def test_get_all_categories(self, category_uow):
        """Test fetching all categories for a user"""

        user_id = 1
        mock_categories = [MagicMock(), MagicMock()]
        mock_categories[0].to_dict.return_value = {'id': 1, 'name': 'Food', 'icon': '321'}
        mock_categories[1].to_dict.return_value = {'id': 2, 'name': 'Transport', 'icon': '123'}
        category_uow.categories.get_all_categories.return_value = mock_categories

        service = CategoryService(category_uow)
        result = service.get_all_categories(user_id)

        category_uow.categories.get_all_categories.assert_called_once_with(user_id)
        assert result == [{'id': 1, 'name': 'Food', 'icon': '321'}, {'id': 2, 'name': 'Transport', 'icon': '123'}]

    def test_get_all_categories_no_categories(self, category_uow):
        """Test fetching categories when user has no categories"""

        user_id = 1
        category_uow.categories.get_all_categories.return_value = []

        service = CategoryService(category_uow)
        result = service.get_all_categories(user_id)

        category_uow.categories.get_all_categories.assert_called_once_with(user_id)
        assert result == []

    def test_get_all_categories_user_not_found(self, category_uow):
        """Test fetching categories for a non-existent user"""

        user_id = 999
        category_uow.categories.get_all_categories.return_value = []

        service = CategoryService(category_uow)
        result = service.get_all_categories(user_id)

        category_uow.categories.get_all_categories.assert_called_once_with(user_id)
        assert result == []


SUCCESS_CATEGORY_DATA = {'name': 'Food', 'icon': 'bi-tag-fill'}

class TestCreateCategory:

    def test_create_category_success(self, category_uow):
        """Test successful category creation without mcc_code"""

        user_id = 1
        category_data = SUCCESS_CATEGORY_DATA
        new_category = MagicMock()
        new_category.to_dict.return_value = {'id': 1, 'name': 'Food', 'icon': '321'}
        category_uow.categories.get_count_by_user.return_value = 0
        category_uow.categories.get_by_name_and_user.return_value = None
        category_uow.categories.create_category.return_value = new_category

        service = CategoryService(category_uow)
        result = service.create_category(user_id, category_data)

        category_uow.categories.get_count_by_user.assert_called_once_with(user_id)
        category_uow.categories.get_by_name_and_user.assert_called_once_with('Food', user_id)
        category_uow.categories.create_category.assert_called_once()
        assert result == new_category

        assert category_uow.flush.call_count == 1
        assert category_uow.on_commit.call_count == 2

    def test_create_category_success_with_mcc_code(self, category_uow):
        """Test successful category creation with mcc_code"""

        user_id = 1
        category_data = {**SUCCESS_CATEGORY_DATA, 'mcc_code': '1234'}
        new_category = MagicMock()
        new_category.to_dict.return_value = {'id': 1, 'name': 'Food', 'icon': '321', 'mcc_code': '1234'}
        category_uow.categories.get_count_by_user.return_value = 0
        category_uow.categories.get_by_name_and_user.return_value = None
        category_uow.categories.create_category.return_value = new_category

        service = CategoryService(category_uow)
        result = service.create_category(user_id, category_data)

        category_uow.categories.get_count_by_user.assert_called_once_with(user_id)
        category_uow.categories.get_by_name_and_user.assert_called_once_with('Food', user_id)
        category_uow.categories.create_category.assert_called_once()
        assert result == new_category

        assert category_uow.flush.call_count == 1
        assert category_uow.on_commit.call_count == 2

    def test_create_category_duplicate_name(self, category_uow):
        """Test category creation with a duplicate name"""

        user_id = 1
        category_data = SUCCESS_CATEGORY_DATA
        existing_category = MagicMock()
        category_uow.categories.get_count_by_user.return_value = 0
        category_uow.categories.get_by_name_and_user.return_value = existing_category

        service = CategoryService(category_uow)

        with pytest.raises(ConflictError) as exc_info:
            service.create_category(user_id, category_data)

        category_uow.categories.get_count_by_user.assert_called_once_with(user_id)
        category_uow.categories.get_by_name_and_user.assert_called_once_with('Food', user_id)
        category_uow.categories.create_category.assert_not_called()
        assert "already exists" in str(exc_info.value)
        assert "Category with name Food already exists" in str(exc_info.value)
        assert category_uow.flush.call_count == 0
        assert category_uow.on_commit.call_count == 0

    def test_create_category_max_limit_reached(self, category_uow):
        """Test category creation when user has reached max category limit"""

        user_id = 1
        category_data = SUCCESS_CATEGORY_DATA
        category_uow.categories.get_count_by_user.return_value = 10  # Simulate max limit reached

        service = CategoryService(category_uow)

        with pytest.raises(BusinessLogicError) as exc_info:
            service.create_category(user_id, category_data)

        category_uow.categories.get_count_by_user.assert_called_once_with(user_id)
        category_uow.categories.get_by_name_and_user.assert_not_called()
        category_uow.categories.create_category.assert_not_called()
        assert "limit of 10 categories" in str(exc_info.value)
        assert category_uow.flush.call_count == 0
        assert category_uow.on_commit.call_count == 0


    @pytest.mark.parametrize("invalid_data", [
        SUCCESS_CATEGORY_DATA | {'name': ''},  # Empty name
        SUCCESS_CATEGORY_DATA | {'mcc_code': 'x' * 129},  # MCC code too long
        SUCCESS_CATEGORY_DATA | {'name': 'x' * 51},  # Name too long
        SUCCESS_CATEGORY_DATA | {'icon': 'x' * 51},  # Icon
        SUCCESS_CATEGORY_DATA | {'name': None},  # Name is None
        SUCCESS_CATEGORY_DATA | {'icon': None},  # Icon is None (should default to 'bi-tag-fill')
    ])
    def test_create_cat_validation_error(self, category_uow, invalid_data):
        """Test category creation with various validation errors"""

        user_id = 1
        category_uow.categories.get_count_by_user.return_value = 0
        category_uow.categories.get_by_name_and_user.return_value = None

        service = CategoryService(category_uow)

        with pytest.raises(ValidationError) as exc_info:
            service.create_category(user_id, invalid_data)

        category_uow.categories.get_count_by_user.assert_not_called()
        category_uow.categories.get_by_name_and_user.assert_not_called()
        category_uow.categories.create_category.assert_not_called()
        assert category_uow.flush.call_count == 0
        assert category_uow.on_commit.call_count == 0

    def test_create_cat_invalid_icon(self, category_uow):
        """Test category creation with an invalid icon"""

        user_id = 1
        category_data = SUCCESS_CATEGORY_DATA | {'icon': 'invalid-icon'}
        category_uow.categories.get_count_by_user.return_value = 0
        category_uow.categories.get_by_name_and_user.return_value = None

        service = CategoryService(category_uow)

        with pytest.raises(BusinessLogicError) as exc_info:
            service.create_category(user_id, category_data)

        category_uow.categories.get_count_by_user.assert_not_called()
        category_uow.categories.get_by_name_and_user.assert_not_called()
        category_uow.categories.create_category.assert_not_called()
        assert "Icon invalid-icon is not allowed" in str(exc_info.value)
        assert category_uow.flush.call_count == 0
        assert category_uow.on_commit.call_count == 0

class TestUpdateCategory:
    
    def test_update_category_success(self, category_uow):
        """Test successful category update"""

        user_id = 1
        cat_id = 1
        update_data = {'name': 'Updated Name', 'icon': 'bi-tag-fill'}
        cat_to_update = MagicMock(**SUCCESS_CATEGORY_DATA)

        category_uow.categories.get_by_id_and_user.return_value = cat_to_update
        category_uow.categories.get_by_name_and_user.return_value = None  
        category_uow.categories.update_category.return_value = cat_to_update

        service = CategoryService(category_uow)
        result = service.update_category(user_id, update_data, cat_id)

        category_uow.categories.get_by_id_and_user.assert_called_once_with(cat_id, user_id)
        category_uow.categories.update_category.assert_called_once()
        assert result == cat_to_update
        assert category_uow.on_commit.call_count == 3
        
    @pytest.mark.parametrize("invalid_data", [
        {'name': ''},  # Empty name
        {'name': 'x' * 51},  # Name too long
        {'icon': 'x' * 51},  # Icon too long
    ])
    def test_update_category_validation_error(self, category_uow, invalid_data):
        """Test category update with validation errors"""

        user_id = 1
        cat_id = 1

        service = CategoryService(category_uow)

        with pytest.raises(ValidationError) as exc_info:
            service.update_category(user_id, invalid_data, cat_id)
        
        category_uow.categories.get_by_id_and_user.assert_not_called()
        category_uow.categories.update_category.assert_not_called()
        assert category_uow.on_commit.call_count == 0

    def test_update_cat_invalid_icon(self, category_uow):
        """Test category update with invalid icon"""

        user_id = 1
        cat_id = 1
        update_data = {'icon': 'invalid-icon'}

        service = CategoryService(category_uow)

        with pytest.raises(BusinessLogicError) as exc_info:
            service.update_category(user_id, update_data, cat_id)
        
        category_uow.categories.get_by_id_and_user.assert_not_called()
        category_uow.categories.update_category.assert_not_called()
        assert "Icon invalid-icon is not allowed" in str(exc_info.value)
        assert category_uow.on_commit.call_count == 0
        
    def test_update_category_not_found(self, category_uow):
        """Test category update when category is not found or access denied"""

        user_id = 1
        cat_id = 999
        update_data = {'name': 'Updated Name'}

        category_uow.categories.get_by_id_and_user.return_value = None

        service = CategoryService(category_uow)

        with pytest.raises(ResourceNotFound) as exc_info:
            service.update_category(user_id, update_data, cat_id)
        
        category_uow.categories.get_by_id_and_user.assert_called_once_with(cat_id, user_id)
        category_uow.categories.update_category.assert_not_called()
        assert "Category 999 not found or access denied" in str(exc_info.value)
        assert category_uow.on_commit.call_count == 0

    def test_update_uncategorized_category_name(self, category_uow):
        """Test that renaming the 'Uncategorized' category is not allowed"""

        user_id = 1
        cat_id = 1
        update_data = {'name': 'New Name'}
        cat_to_update = MagicMock(icon='bi-tag-fill')
        cat_to_update.name = 'Uncategorized'

        category_uow.categories.get_by_id_and_user.return_value = cat_to_update

        service = CategoryService(category_uow)
        with pytest.raises(BusinessLogicError) as exc_info:
            service.update_category(user_id, update_data, cat_id)
        
        category_uow.categories.get_by_id_and_user.assert_called_once_with(cat_id, user_id)
        category_uow.categories.update_category.assert_not_called()
        assert "Cannot rename the default 'Uncategorized' category" in str(exc_info.value)
        assert category_uow.on_commit.call_count == 0

    def test_update_category_duplicate_name(self, category_uow):
        """Test that updating a category to a name that already exists for the user is not allowed"""

        user_id = 1
        cat_id = 1
        update_data = {'name': 'Existing Category'}
        cat_to_update = MagicMock(**SUCCESS_CATEGORY_DATA)
        existing_category = MagicMock(id=2)

        category_uow.categories.get_by_id_and_user.return_value = cat_to_update
        category_uow.categories.get_by_name_and_user.return_value = existing_category

        service = CategoryService(category_uow)
        with pytest.raises(ConflictError) as exc_info:
            service.update_category(user_id, update_data, cat_id)
        
        category_uow.categories.get_by_id_and_user.assert_called_once_with(cat_id, user_id)
        category_uow.categories.get_by_name_and_user.assert_called_once_with('Existing Category', user_id)
        category_uow.categories.update_category.assert_not_called()
        assert "Category with name Existing Category already exists" in str(exc_info.value)
        assert category_uow.on_commit.call_count == 0

    def test_update_category_no_valid_changes(self, category_uow):
        """Test that if no valid changes are provided, the category is not updated"""

        user_id = 1
        cat_id = 1
        update_data = {}  # No changes provided
        cat_to_update = MagicMock(**SUCCESS_CATEGORY_DATA)

        category_uow.categories.get_by_id_and_user.return_value = cat_to_update

        service = CategoryService(category_uow)
        with pytest.raises(BusinessLogicError) as exc_info:
            service.update_category(user_id, update_data, cat_id)
        
        category_uow.categories.get_by_id_and_user.assert_called_once_with(cat_id, user_id)
        assert "No data provided for update" in str(exc_info.value)
        category_uow.categories.update_category.assert_not_called()
        assert category_uow.on_commit.call_count == 0

class TestDeleteCategory:
    def test_delete_category_success(self, category_uow):
        """Test successful category deletion"""

        user_id = 1
        cat_id = 1
        cat_to_delete = MagicMock(**SUCCESS_CATEGORY_DATA)

        category_uow.categories.get_cat_by_id_and_user.return_value = cat_to_delete
        category_uow.transactions.get_count_by_category.return_value = 0 
        category_uow.budget.get_by_category_and_user.return_value = None

        service = CategoryService(category_uow)
        result = service.delete_category(cat_id, user_id)

        category_uow.categories.get_cat_by_id_and_user.assert_called_once_with(cat_id, user_id)
        category_uow.categories.delete_category.assert_called_once_with(cat_to_delete)
        assert result is True
        assert category_uow.on_commit.call_count == 2

    def test_delete_category_not_found(self, category_uow):
        """Test category deletion when category is not found or access denied"""

        user_id = 1
        cat_id = 999

        category_uow.categories.get_cat_by_id_and_user.return_value = None

        service = CategoryService(category_uow)

        with pytest.raises(ResourceNotFound) as exc_info:
            service.delete_category(cat_id, user_id)
        
        category_uow.categories.get_cat_by_id_and_user.assert_called_once_with(cat_id, user_id)
        category_uow.categories.delete_category.assert_not_called()
        assert "Category 999 not found or access denied" in str(exc_info.value)
        assert category_uow.on_commit.call_count == 0

    def test_delete_uncategorized_category(self, category_uow):
        """Test that deleting the 'Uncategorized' category is not allowed"""

        user_id = 1
        cat_id = 1
        cat_to_delete = MagicMock(icon='bi-tag-fill')
        cat_to_delete.name = 'Uncategorized'

        category_uow.categories.get_cat_by_id_and_user.return_value = cat_to_delete
        category_uow.transactions.get_count_by_category.return_value = 0
        category_uow.budget.get_by_category_and_user.return_value = None

        service = CategoryService(category_uow)
        with pytest.raises(BusinessLogicError) as exc_info:
            service.delete_category(cat_id, user_id)
        
        category_uow.categories.get_cat_by_id_and_user.assert_called_once_with(cat_id, user_id)
        category_uow.categories.delete_category.assert_not_called()
        assert "Cannot delete the default 'Uncategorized' category" in str(exc_info.value)
        assert category_uow.on_commit.call_count == 0

    def test_delete_category_with_related_transactions(self, category_uow):
        """Test that deleting a category with related transactions is not allowed"""

        user_id = 1
        cat_id = 1
        cat_to_delete = MagicMock(**SUCCESS_CATEGORY_DATA)

        category_uow.categories.get_cat_by_id_and_user.return_value = cat_to_delete
        category_uow.transactions.get_count_by_category.return_value = 5  # Simulate related transactions

        service = CategoryService(category_uow)
        with pytest.raises(BusinessLogicError) as exc_info:
            service.delete_category(cat_id, user_id)
        
        category_uow.categories.get_cat_by_id_and_user.assert_called_once_with(cat_id, user_id)
        category_uow.transactions.get_count_by_category.assert_called_once_with(user_id, cat_id)
        category_uow.categories.delete_category.assert_not_called()
        assert "Cannot delete category. It has 5 related transactions" in str(exc_info.value)
        assert category_uow.on_commit.call_count == 0

    def test_delete_category_with_related_budgets(self, category_uow):
        """Test that deleting a category associated with budgets is not allowed"""

        user_id = 1
        cat_id = 1
        cat_to_delete = MagicMock(**SUCCESS_CATEGORY_DATA)

        category_uow.categories.get_cat_by_id_and_user.return_value = cat_to_delete
        category_uow.transactions.get_count_by_category.return_value = 0  # No related transactions
        category_uow.budget.get_by_category_and_user.return_value = MagicMock()  # Simulate related budget

        service = CategoryService(category_uow)
        with pytest.raises(BusinessLogicError) as exc_info:
            service.delete_category(cat_id, user_id)
        
        category_uow.categories.get_cat_by_id_and_user.assert_called_once_with(cat_id, user_id)
        category_uow.transactions.get_count_by_category.assert_called_once_with(user_id, cat_id)
        category_uow.budget.get_by_category_and_user.assert_called_once_with(user_id, cat_id)
        category_uow.categories.delete_category.assert_not_called()
        assert "Cannot delete category. It is associated with existing budgets" in str(exc_info.value)
        assert category_uow.on_commit.call_count == 0

    def test_delete_category_not_found(self, category_uow):
        """Test category deletion when category is not found or access denied"""

        user_id = 1
        cat_id = 999

        category_uow.categories.get_cat_by_id_and_user.return_value = None

        service = CategoryService(category_uow)

        with pytest.raises(ResourceNotFound) as exc_info:
            service.delete_category(cat_id, user_id)
        
        category_uow.categories.get_cat_by_id_and_user.assert_called_once_with(cat_id, user_id)
        category_uow.categories.delete_category.assert_not_called()
        assert "Category 999 not found or access denied" in str(exc_info.value)
        assert category_uow.on_commit.call_count == 0

    def test_delete_category_with_related_transactions_and_budgets(self, category_uow):
        """Test that deleting a category with both related transactions and budgets is not allowed"""

        user_id = 1
        cat_id = 1
        cat_to_delete = MagicMock(**SUCCESS_CATEGORY_DATA)

        category_uow.categories.get_cat_by_id_and_user.return_value = cat_to_delete
        category_uow.transactions.get_count_by_category.return_value = 5 
        category_uow.budget.get_by_category_and_user.return_value = MagicMock() 

        service = CategoryService(category_uow)
        with pytest.raises(BusinessLogicError) as exc_info:
            service.delete_category(cat_id, user_id)
        
        category_uow.categories.get_cat_by_id_and_user.assert_called_once_with(cat_id, user_id)
        category_uow.transactions.get_count_by_category.assert_called_once_with(user_id, cat_id)
        category_uow.budget.get_by_category_and_user.assert_not_called()  
        category_uow.categories.delete_category.assert_not_called()
        assert "Cannot delete category. It has 5 related transactions" in str(exc_info.value)
        assert category_uow.on_commit.call_count == 0

    



        