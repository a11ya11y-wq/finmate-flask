
from backend.finmate.categories.repository import CategoryRepository
from .schemas import CategoryCreateSchema, CategoryUpdateSchema
from backend.finmate.exceptions import ConflictError, BusinessLogicError, ResourceNotFound
from backend.finmate.utils.caching import redis_cache, invalidate_cache
from backend.finmate.constants import ALLOWED_ICONS, MAX_CATEGORIES_PER_USER
from backend.finmate.transactions.repository import TransactionRepository



def categories_key_builder(self, user_id):
    return f"categories:{user_id}"


class CategoryService:

    def __init__(self):
        self.repo = CategoryRepository()
        self.repo_tx = TransactionRepository()

    @redis_cache(ttl=86400, key_builder=categories_key_builder)
    def get_all_categories(self, user_id):
        cat_objects =  self.repo.get_all_categories(user_id)

        return [cat.to_dict() for cat in cat_objects]

    def create_category(self, user_id, data):

        if MAX_CATEGORIES_PER_USER <= self.repo.get_count_by_user(user_id):
            raise BusinessLogicError(f'You have reached the limit of {MAX_CATEGORIES_PER_USER} categories')

        validated_data = CategoryCreateSchema.model_validate(data)

        name = validated_data.name
        existing_category = self.repo.get_by_name_and_user(name, user_id)

        if existing_category:
            raise ConflictError(f"Category with name {name} already exists.")

        if validated_data.icon not in ALLOWED_ICONS:
            raise BusinessLogicError(f"Icon {validated_data.icon} is not allowed.")

        payload = validated_data.model_dump()
        payload['user_id'] = user_id

        new_cat = self.repo.create_category(payload)

        self._clear_related_caches(user_id)
        return new_cat


    def update_category(self, user_id, data, cat_id):
        cat_to_update = self.repo.get_cat_by_id_and_user(cat_id, user_id)

        if not cat_to_update:
            raise ResourceNotFound(f"Category {cat_to_update} not found or access denied.")

        validated_data = CategoryUpdateSchema.model_validate(data)

        if validated_data.name:
            existing_category = self.repo.get_by_name_and_user(validated_data.name, user_id)
            if existing_category and existing_category.id != cat_id:
                raise ConflictError(f"Category with name {validated_data.name} already exists.")

            if validated_data.icon and validated_data.icon not in ALLOWED_ICONS:
                raise BusinessLogicError(f"Icon {validated_data.icon} is not allowed.")

        payload = validated_data.model_dump(exclude_unset=True)
        if not payload:
            raise BusinessLogicError("No data provided for update.")

        updated_cat = self.repo.update_category(cat_to_update, payload)

        self._clear_related_caches(user_id)
        return updated_cat


    def delete_category(self, cat_id, user_id):
        cat_to_delete = self.repo.get_cat_by_id_and_user(cat_id, user_id)

        if not cat_to_delete:
            raise ResourceNotFound(f"Category {cat_id} not found or access denied.")

        count_tx = self.repo_tx.get_count_by_category(user_id, cat_id)
        if count_tx > 0:
            raise BusinessLogicError(f"Cannot delete category. It has {count_tx} related transactions.")

        self.repo.delete_category(cat_to_delete)

        self._clear_related_caches(user_id)
        return True


    @staticmethod
    def _clear_related_caches(user_id):
        invalidate_cache(f"categories:{user_id}")
        invalidate_cache(f"dashboard:{user_id}:*")