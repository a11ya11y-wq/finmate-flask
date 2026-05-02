from typing import Optional

from core_service.extensions import db
from core_service.models import Category


class CategoryRepository:

    def get_all_categories(self, user_id: int) -> list[Category]:
        return Category.query.filter_by(user_id=user_id).all()

    def get_cat_by_id(self, cat_id: int) -> Optional[Category]:
        return Category.query.get(cat_id)

    def get_cat_by_id_and_user(self, cat_id: int, user_id: int) -> Optional[Category]:
        return Category.query.filter_by(id=cat_id, user_id=user_id).first()

    def get_count_by_user(self, user_id: int) -> int:
        return Category.query.filter_by(user_id=user_id).count()

    def get_by_name_and_user(self, name: str, user_id: int) -> Optional[Category]:
        return Category.query.filter_by(
            name=name,
            user_id=user_id
        ).first()

    def get_by_id_and_user(self, category_id: int, user_id: int) -> Optional[Category]:
        return Category.query.filter_by(
            id=category_id,
            user_id=user_id
        ).first()

    def create_category(self, data: dict) -> Category:
        new_category = Category(
            name=data.get('name'),
            user_id=data.get('user_id'),
            icon=data.get('icon'),
            mcc_code=data.get('mcc_code')
        )
        db.session.add(new_category)
        return new_category

    def update_category(self, cat_obj: Category, data: dict) -> Category:
        cat_obj.name = data.get('name', cat_obj.name)
        cat_obj.icon = data.get('icon', cat_obj.icon)
        cat_obj.mcc_code = data.get('mcc_code', cat_obj.mcc_code)
        return cat_obj

    def delete_category(self, cat_obj: Category) -> None:
        db.session.delete(cat_obj)
