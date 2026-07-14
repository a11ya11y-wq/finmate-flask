from unittest.mock import MagicMock

import allure
import pytest
from core_service.categories.service import CategoryService
from core_service.exceptions import BusinessLogicError, ConflictError, ResourceNotFound
from pydantic import ValidationError


@pytest.fixture
@allure.title("Initialize Mocked Category UOW")
def category_uow():
    with allure.step("Initialize MagicMock for Category Unit of Work"):
        return MagicMock()


SUCCESS_CATEGORY_DATA = {"name": "Food", "icon": "bi-tag-fill"}


@allure.feature("Category Management")
@allure.story("Retrieve Categories")
class TestGetCategories:

    @allure.title("Retrieve all categories for a user")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_get_all_categories(self, category_uow):
        with allure.step("Arrange: Mock user categories"):
            user_id = 1
            mock_categories = [MagicMock(), MagicMock()]
            mock_categories[0].to_dict.return_value = {
                "id": 1,
                "name": "Food",
                "icon": "321",
            }
            mock_categories[1].to_dict.return_value = {
                "id": 2,
                "name": "Transport",
                "icon": "123",
            }
            category_uow.categories.get_all_categories.return_value = mock_categories

        with allure.step("Act: Fetch categories"):
            service = CategoryService(category_uow)
            result = service.get_all_categories(user_id)

        with allure.step("Assert: Verify returned list"):
            category_uow.categories.get_all_categories.assert_called_once_with(user_id)
            assert result == [
                {"id": 1, "name": "Food", "icon": "321"},
                {"id": 2, "name": "Transport", "icon": "123"},
            ]

    @allure.title("Return empty list when user has no categories")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_all_categories_no_categories(self, category_uow):
        with allure.step("Arrange: Mock empty category list"):
            user_id = 1
            category_uow.categories.get_all_categories.return_value = []

        with allure.step("Act & Assert"):
            service = CategoryService(category_uow)
            result = service.get_all_categories(user_id)
            assert result == []

    @allure.title("Return empty list for a non-existent user")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_all_categories_user_not_found(self, category_uow):
        with allure.step("Arrange: Mock user not found"):
            user_id = 999
            category_uow.categories.get_all_categories.return_value = []

        with allure.step("Act & Assert"):
            service = CategoryService(category_uow)
            result = service.get_all_categories(user_id)
            assert result == []


@allure.feature("Category Management")
@allure.story("Create Category")
class TestCreateCategory:

    @allure.title("Successfully create category without MCC code")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_create_category_success(self, category_uow):
        with allure.step("Arrange: Mock boundaries and category creation"):
            user_id = 1
            category_data = SUCCESS_CATEGORY_DATA
            new_category = MagicMock()
            new_category.to_dict.return_value = {"id": 1, "name": "Food", "icon": "321"}
            category_uow.categories.get_count_by_user.return_value = 0
            category_uow.categories.get_by_name_and_user.return_value = None
            category_uow.categories.create_category.return_value = new_category

        with allure.step("Act: Call create_category"):
            service = CategoryService(category_uow)
            result = service.create_category(user_id, category_data)

        with allure.step("Assert: Verify commit calls and created category"):
            category_uow.categories.create_category.assert_called_once()
            assert result == new_category
            assert category_uow.flush.call_count == 1
            assert category_uow.on_commit.call_count == 2

    @allure.title("Successfully create category with MCC code")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_category_success_with_mcc_code(self, category_uow):
        with allure.step("Arrange: Mock creation including MCC"):
            user_id = 1
            category_data = {**SUCCESS_CATEGORY_DATA, "mcc_code": "1234"}
            new_category = MagicMock()
            new_category.to_dict.return_value = {
                "id": 1,
                "name": "Food",
                "icon": "321",
                "mcc_code": "1234",
            }
            category_uow.categories.get_count_by_user.return_value = 0
            category_uow.categories.get_by_name_and_user.return_value = None
            category_uow.categories.create_category.return_value = new_category

        with allure.step("Act & Assert"):
            service = CategoryService(category_uow)
            result = service.create_category(user_id, category_data)
            assert result == new_category

    @allure.title("Fail to create category with duplicate name")
    @allure.severity(allure.severity_level.NORMAL)
    def test_create_category_duplicate_name(self, category_uow):
        with allure.step("Arrange: Mock existing category"):
            user_id = 1
            category_data = SUCCESS_CATEGORY_DATA
            existing_category = MagicMock()
            category_uow.categories.get_count_by_user.return_value = 0
            category_uow.categories.get_by_name_and_user.return_value = (
                existing_category
            )

        with allure.step("Act & Assert: Expect ConflictError"):
            service = CategoryService(category_uow)
            with pytest.raises(
                ConflictError, match="Category with name Food already exists"
            ):
                service.create_category(user_id, category_data)

    @allure.title("Fail to create category when max limit reached")
    @allure.severity(allure.severity_level.NORMAL)
    def test_create_category_max_limit_reached(self, category_uow):
        with allure.step("Arrange: Mock limit reached"):
            user_id = 1
            category_data = SUCCESS_CATEGORY_DATA
            category_uow.categories.get_count_by_user.return_value = 10

        with allure.step("Act & Assert: Expect BusinessLogicError"):
            service = CategoryService(category_uow)
            with pytest.raises(BusinessLogicError, match="limit of 10 categories"):
                service.create_category(user_id, category_data)

    @allure.title("Validation errors on invalid payload during creation")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize(
        "invalid_data",
        [
            SUCCESS_CATEGORY_DATA | {"name": ""},
            SUCCESS_CATEGORY_DATA | {"mcc_code": "x" * 129},
            SUCCESS_CATEGORY_DATA | {"name": "x" * 51},
            SUCCESS_CATEGORY_DATA | {"icon": "x" * 51},
            SUCCESS_CATEGORY_DATA | {"name": None},
            SUCCESS_CATEGORY_DATA | {"icon": None},
        ],
    )
    def test_create_cat_validation_error(self, category_uow, invalid_data):
        with allure.step("Arrange: Setup valid baseline"):
            user_id = 1
            category_uow.categories.get_count_by_user.return_value = 0
            category_uow.categories.get_by_name_and_user.return_value = None

        with allure.step("Act & Assert: Expect ValidationError"):
            service = CategoryService(category_uow)
            with pytest.raises(ValidationError):
                service.create_category(user_id, invalid_data)

    @allure.title("Fail to create category with invalid icon")
    @allure.severity(allure.severity_level.NORMAL)
    def test_create_cat_invalid_icon(self, category_uow):
        with allure.step("Arrange: Set invalid icon"):
            user_id = 1
            category_data = SUCCESS_CATEGORY_DATA | {"icon": "invalid-icon"}
            category_uow.categories.get_count_by_user.return_value = 0
            category_uow.categories.get_by_name_and_user.return_value = None

        with allure.step("Act & Assert: Expect BusinessLogicError"):
            service = CategoryService(category_uow)
            with pytest.raises(
                BusinessLogicError, match="Icon invalid-icon is not allowed"
            ):
                service.create_category(user_id, category_data)


@allure.feature("Category Management")
@allure.story("Update Category")
class TestUpdateCategory:

    @allure.title("Successfully update an existing category")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_update_category_success(self, category_uow):
        with allure.step("Arrange: Mock existing category and update data"):
            user_id = 1
            cat_id = 1
            update_data = {"name": "Updated Name", "icon": "bi-tag-fill"}
            cat_to_update = MagicMock(**SUCCESS_CATEGORY_DATA)
            category_uow.categories.get_by_id_and_user.return_value = cat_to_update
            category_uow.categories.get_by_name_and_user.return_value = None
            category_uow.categories.update_category.return_value = cat_to_update

        with allure.step("Act: Call update_category"):
            service = CategoryService(category_uow)
            result = service.update_category(user_id, update_data, cat_id)

        with allure.step("Assert: Verify commit calls"):
            category_uow.categories.update_category.assert_called_once()
            assert result == cat_to_update
            assert category_uow.on_commit.call_count == 3

    @allure.title("Fail to rename the 'Uncategorized' default category")
    @allure.severity(allure.severity_level.NORMAL)
    def test_update_uncategorized_category_name(self, category_uow):
        with allure.step("Arrange: Mock 'Uncategorized' category update attempt"):
            user_id = 1
            cat_id = 1
            update_data = {"name": "New Name"}
            cat_to_update = MagicMock(icon="bi-tag-fill")
            cat_to_update.name = "Uncategorized"
            category_uow.categories.get_by_id_and_user.return_value = cat_to_update

        with allure.step("Act & Assert: Expect BusinessLogicError"):
            service = CategoryService(category_uow)
            with pytest.raises(
                BusinessLogicError,
                match="Cannot rename the default 'Uncategorized' category",
            ):
                service.update_category(user_id, update_data, cat_id)

    @allure.title("Fail to update category if new name is duplicated")
    @allure.severity(allure.severity_level.NORMAL)
    def test_update_category_duplicate_name(self, category_uow):
        with allure.step("Arrange: Mock existing duplicate"):
            user_id = 1
            cat_id = 1
            update_data = {"name": "Existing Category"}
            cat_to_update = MagicMock(**SUCCESS_CATEGORY_DATA)
            existing_category = MagicMock(id=2)
            category_uow.categories.get_by_id_and_user.return_value = cat_to_update
            category_uow.categories.get_by_name_and_user.return_value = (
                existing_category
            )

        with allure.step("Act & Assert: Expect ConflictError"):
            service = CategoryService(category_uow)
            with pytest.raises(
                ConflictError,
                match="Category with name Existing Category already exists",
            ):
                service.update_category(user_id, update_data, cat_id)


@allure.feature("Category Management")
@allure.story("Delete Category")
class TestDeleteCategory:

    @allure.title("Successfully delete a category")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_category_success(self, category_uow):
        with allure.step("Arrange: Mock dependencies free of links (tx/budget)"):
            user_id = 1
            cat_id = 1
            cat_to_delete = MagicMock(**SUCCESS_CATEGORY_DATA)
            category_uow.categories.get_cat_by_id_and_user.return_value = cat_to_delete
            category_uow.transactions.get_count_by_category.return_value = 0
            category_uow.budget.get_by_category_and_user.return_value = None

        with allure.step("Act: Call delete_category"):
            service = CategoryService(category_uow)
            result = service.delete_category(cat_id, user_id)

        with allure.step("Assert: Verify deletion was called"):
            category_uow.categories.delete_category.assert_called_once_with(
                cat_to_delete
            )
            assert result is True

    @allure.title("Fail to delete the 'Uncategorized' default category")
    @allure.severity(allure.severity_level.NORMAL)
    def test_delete_uncategorized_category(self, category_uow):
        with allure.step("Arrange: Mock default category"):
            user_id = 1
            cat_id = 1
            cat_to_delete = MagicMock(icon="bi-tag-fill")
            cat_to_delete.name = "Uncategorized"
            category_uow.categories.get_cat_by_id_and_user.return_value = cat_to_delete
            category_uow.transactions.get_count_by_category.return_value = 0
            category_uow.budget.get_by_category_and_user.return_value = None

        with allure.step("Act & Assert: Expect BusinessLogicError"):
            service = CategoryService(category_uow)
            with pytest.raises(
                BusinessLogicError,
                match="Cannot delete the default 'Uncategorized' category",
            ):
                service.delete_category(cat_id, user_id)

    @allure.title("Fail to delete category with related transactions")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_category_with_related_transactions(self, category_uow):
        with allure.step("Arrange: Mock related transactions existence"):
            user_id = 1
            cat_id = 1
            cat_to_delete = MagicMock(**SUCCESS_CATEGORY_DATA)
            category_uow.categories.get_cat_by_id_and_user.return_value = cat_to_delete
            category_uow.transactions.get_count_by_category.return_value = 5

        with allure.step("Act & Assert: Expect BusinessLogicError"):
            service = CategoryService(category_uow)
            with pytest.raises(
                BusinessLogicError,
                match="Cannot delete category. It has 5 related transactions",
            ):
                service.delete_category(cat_id, user_id)

    @allure.title("Fail to delete category with related budgets")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_category_with_related_budgets(self, category_uow):
        with allure.step("Arrange: Mock related budgets existence"):
            user_id = 1
            cat_id = 1
            cat_to_delete = MagicMock(**SUCCESS_CATEGORY_DATA)
            category_uow.categories.get_cat_by_id_and_user.return_value = cat_to_delete
            category_uow.transactions.get_count_by_category.return_value = 0
            category_uow.budget.get_by_category_and_user.return_value = MagicMock()

        with allure.step("Act & Assert: Expect BusinessLogicError"):
            service = CategoryService(category_uow)
            with pytest.raises(
                BusinessLogicError,
                match="Cannot delete category. It is associated with existing budgets",
            ):
                service.delete_category(cat_id, user_id)
