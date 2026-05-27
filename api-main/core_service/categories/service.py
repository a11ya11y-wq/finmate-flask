import logging

from core_service.constants import ALLOWED_ICONS, MAX_CATEGORIES_PER_USER
from core_service.exceptions import ConflictError, BusinessLogicError, ResourceNotFound
from core_service.models.category_model import Category
from core_service.uow import UnitOfWork
from core_service.utils.caching import redis_cache, invalidate_cache
from .schemas import CategoryCreateSchema, CategoryUpdateSchema

logger = logging.getLogger(__name__)


def categories_key_builder(self, user_id):
    return f"categories:{user_id}"


class CategoryService:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    @redis_cache(ttl=86400, key_builder=categories_key_builder)
    def get_all_categories(self, user_id: int) -> list[Category]:

        cat_objects =  self.uow.categories.get_all_categories(user_id)

        return [cat.to_dict() for cat in cat_objects]

    def create_category(self, user_id: int, data: dict) -> Category:

        validated_data = CategoryCreateSchema.model_validate(data)

        if validated_data.icon not in ALLOWED_ICONS:
            logger.warning(f"Category creation failed: invalid icon {validated_data.icon} for user {user_id}")
            raise BusinessLogicError(f"Icon {validated_data.icon} is not allowed.")

        name = validated_data.name
        payload = validated_data.model_dump()
        payload['user_id'] = user_id

        if MAX_CATEGORIES_PER_USER <= self.uow.categories.get_count_by_user(user_id):
            raise BusinessLogicError(f'You have reached the limit of {MAX_CATEGORIES_PER_USER} categories')

        existing_category = self.uow.categories.get_by_name_and_user(name, user_id)

        if existing_category:
            logger.warning(f"Category creation failed: duplicate name {name} for user {user_id}")
            raise ConflictError(f"Category with name {name} already exists.")

        new_cat = self.uow.categories.create_category(payload)
        self.uow.flush()
        try:
            self._clear_related_caches(user_id)
            logger.info(f"New category created for user {user_id} with name {name}")
        except Exception as e:
            logger.error(f"Post-commit action failed: {e}")
        return new_cat

    def update_category(self, user_id: int, data: dict, cat_id: int) -> Category:

        validated_data = CategoryUpdateSchema.model_validate(data)
        cat_name = validated_data.name
        cat_icon = validated_data.icon

        if cat_icon and cat_icon not in ALLOWED_ICONS:
            logger.warning(f"Category update failed: invalid icon {cat_icon} for user {user_id}")
            raise BusinessLogicError(f"Icon {cat_icon} is not allowed.")
        
        cat_to_update = self.uow.categories.get_by_id_and_user(cat_id, user_id)

        if not cat_to_update:
            logger.warning(f"Attempt to update non-existing category {cat_id} by user {user_id}")
            raise ResourceNotFound(f"Category {cat_to_update} not found or access denied.")

        if cat_to_update.name.strip().lower() == "uncategorized":
            if validated_data.name and validated_data.name.strip().lower() != "uncategorized":
                raise BusinessLogicError("Cannot rename the default 'Uncategorized' category.")

        if cat_name:
            existing_category = self.uow.categories.get_by_name_and_user(cat_name, user_id)
            if existing_category and existing_category.id != cat_id:
                logger.warning(f"Category update failed: duplicate name {cat_name} for user {user_id}")
                raise ConflictError(f"Category with name {cat_name} already exists.")

        payload = validated_data.model_dump(exclude_unset=True)
        if not payload:
            raise BusinessLogicError("No data provided for update.")

        updated_cat = self.uow.categories.update_category(cat_to_update, payload)
        try:
            self._clear_related_caches(user_id)
            invalidate_cache(f"budgets:{user_id}")
            logger.info(f"Category {cat_id} updated for user {user_id}")
        except Exception as e:
            logger.error(f"Post-commit action failed: {e}")
        return updated_cat

    def delete_category(self, cat_id: int, user_id: int) -> bool:

        cat_to_delete = self.uow.categories.get_cat_by_id_and_user(cat_id, user_id)

        if not cat_to_delete:
            logger.warning(f"Attempt to delete non-existing category {cat_id} by user {user_id}")
            raise ResourceNotFound(f"Category {cat_id} not found or access denied.")

        count_tx = self.uow.transactions.get_count_by_category(user_id, cat_id)
        if count_tx > 0:
            raise BusinessLogicError(f"Cannot delete category. It has {count_tx} related transactions.")

        if cat_to_delete.name.strip().lower() == "uncategorized":
            raise BusinessLogicError("Cannot delete the default 'Uncategorized' category.")

        budget_exist = self.uow.budget.get_by_category_and_user(user_id, cat_id)
        if budget_exist:
            raise BusinessLogicError("Cannot delete category. It is associated with existing budgets.")

        self.uow.categories.delete_category(cat_to_delete)
        try:
            self._clear_related_caches(user_id)
            logger.info(f"Category {cat_id} deleted for user {user_id}")
        except Exception as e:
            logger.error(f"Post-commit action failed: {e}")
        return True

    @staticmethod
    def _clear_related_caches(user_id):
        invalidate_cache(f"categories:{user_id}")
        invalidate_cache(f"dashboard:{user_id}:*")
