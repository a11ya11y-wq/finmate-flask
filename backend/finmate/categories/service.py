from pydantic import ValidationError

from backend.finmate.categories.repository import CategoryRepository
from .schemas import CategoryCreateSchema, CategoryUpdateSchema



class CategoryService:

    def __init__(self):
        self.repo = CategoryRepository()
        self.MAX_CATEGORIES_PER_USER = 10 #TODO: Замінити на імпорт з config


    def get_all_categories(self, user_id):
        return self.repo.get_all_categories(user_id)


    def create_category(self, user_id, data):

        if self.MAX_CATEGORIES_PER_USER <= self.repo.get_count_by_user(user_id):
            raise PermissionError(f'You have reached the limit of {self.MAX_CATEGORIES_PER_USER} categories')

        try:
            validated_data = CategoryCreateSchema.model_validate(data)
        except ValidationError as e:
            raise ValueError(e.errors())

        name = validated_data.name
        existing_category = self.repo.get_by_name_and_user(name, user_id)

        if existing_category:
            raise FileExistsError(f"Category with name {name} already exists.")

        payload = validated_data.model_dump()
        payload['user_id'] = user_id

        new_cat = self.repo.create_category(payload)

        return new_cat


    def update_category(self, user_id, data, cat_id):
        cat_to_update = self.repo.get_cat_by_id_and_user(cat_id, user_id)

        if not cat_to_update:
            raise PermissionError(f"Category {cat_to_update} not found or access denied.")

        try:
            validated_data = CategoryUpdateSchema.model_validate(data)
        except ValidationError as e:
            raise ValueError(e.errors())

        if validated_data.name:
            existing_category = self.repo.get_by_name_and_user(validated_data.name, user_id)
            if existing_category and existing_category.id != cat_id:
                raise FileExistsError(f"Category with name {validated_data.name} already exists.")

        payload = validated_data.model_dump(exclude_unset=True)

        updated_cat = self.repo.update_category(cat_to_update, payload)

        return updated_cat


    def delete_category(self, cat_id, user_id):
        cat_to_delete = self.repo.get_cat_by_id_and_user(cat_id, user_id)

        if not cat_to_delete:
            raise PermissionError(f"Category {cat_id} not found or access denied.")

        self.repo.delete_category(cat_to_delete)

        return True

