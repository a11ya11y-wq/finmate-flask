from backend.finmate.db import db
from backend.finmate.models import Category


class CategoryRepository:


    def get_all_categories(self, user_id):
        return Category.query.filter_by(user_id=user_id).all()


    def get_cat_by_id(self, cat_id):
        return Category.query.get(cat_id)


    def get_cat_by_id_and_user(self, cat_id, user_id):
        return Category.query.filter_by(id=cat_id, user_id=user_id).first()


    def get_count_by_user(self, user_id):
        return Category.query.filter_by(user_id=user_id).count()

    def get_by_name_and_user(self, name, user_id):
        return Category.query.filter_by(
            name=name,
            user_id=user_id
        ).first()


    def get_by_id_and_user(self, category_id, user_id):
        return Category.query.filter_by(
            id=category_id,
            user_id=user_id
        ).first()


    def create_category(self, data):
        new_category = Category(
            name=data.get('name'),
            user_id=data.get('user_id'),
            mcc_code=data.get('mcc_code')
        )
        try:
            db.session.add(new_category)
            db.session.commit()
            return new_category
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Error while creating category in DB: {e}")


    def update_category(self, cat_obj, data):
        try:
            cat_obj.name = data.get('name', cat_obj.name)
            cat_obj.mcc_code=data.get('mcc_code', cat_obj.mcc_code)
            db.session.commit()
            return cat_obj
        except Exception as e:
            raise Exception(f'Error while updating category in DB: {e}')


    def delete_category(self, cat_obj):
        try:
            db.session.delete(cat_obj)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Error while deleting category in DB: {e}")

