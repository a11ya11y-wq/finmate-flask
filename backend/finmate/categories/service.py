from backend.finmate.categories.repository import CategoryRepository



class CategoryService:

    def __init__(self):
        self.repo = CategoryRepository()


    def get_all_categories(self, user_id):
        return self.repo.get_all_categories(user_id)


    def create_category(self, user_id, data):
        if not data.get('name'):
            raise ValueError('Name is a required field.')

        data['user_id'] = user_id

        new_cat = self.repo.create_category(data)

        return new_cat


    def update_category(self, user_id, data, cat_id):
        cat_to_update = self.repo.get_cat_by_id(cat_id)

        if not cat_to_update:
            raise ValueError(f'Category with {cat_id} not found.')

        if cat_to_update.user_id != int(user_id):
            raise PermissionError("You are not authorized to edit this category.")

        if 'name' in data and not data['name']:
            raise ValueError("Name cannot be empty.")

        updated_cat = self.repo.update_category(cat_to_update, data)

        return updated_cat


    def delete_category(self, cat_id, user_id):
        cat_to_delete = self.repo.get_cat_by_id(cat_id)

        if not cat_to_delete:
            raise ValueError(f"Category with id {cat_id} not found.")

        if cat_to_delete.user_id != int(user_id):
            raise PermissionError('You are not authorized to delete this category.')

        self.repo.delete_category(cat_to_delete)

        return True

