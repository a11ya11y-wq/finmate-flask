from pydantic import ValidationError

from backend.finmate.categories.repository import CategoryRepository
from .schemas import CategoryCreateSchema, CategoryUpdateSchema



class CategoryService:

    def __init__(self):
        self.repo = CategoryRepository()


    def get_all_categories(self, user_id):
        return self.repo.get_all_categories(user_id)


    def create_category(self, user_id, data):

        try:
            validated_data = CategoryCreateSchema.model_validate(data)
        except ValidationError as e:
            raise ValueError(e.errors())

        payload = validated_data.model_dump()

        payload['user_id'] = user_id

        new_cat = self.repo.create_category(payload)

        return new_cat


    def update_category(self, user_id, data, cat_id):
        cat_to_update = self.repo.get_cat_by_id(cat_id)

        if not cat_to_update:
            raise ValueError(f'Category with {cat_id} not found.')

        if cat_to_update.user_id != int(user_id):
            raise PermissionError("You are not authorized to edit this category.")

        try:
            validated_data = CategoryUpdateSchema.model_validate(data)
        except ValidationError as e:
            raise ValueError(e.errors())

        payload = validated_data.model_dump(exclude_unset=True)

        updated_cat = self.repo.update_category(cat_to_update, payload)

        return updated_cat


    def delete_category(self, cat_id, user_id):
        cat_to_delete = self.repo.get_cat_by_id(cat_id)

        if not cat_to_delete:
            raise ValueError(f"Category with id {cat_id} not found.")

        if cat_to_delete.user_id != int(user_id):
            raise PermissionError('You are not authorized to delete this category.')

        self.repo.delete_category(cat_to_delete)

        return True

