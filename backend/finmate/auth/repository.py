from typing import Optional

from finmate.constants import DEFAULT_CATEGORIES
from finmate.extensions import db
from finmate.models import Category, Users


class AuthRepository:

    def find_user_by_name(self, username: str) -> Optional[Users]:
        return Users.query.filter_by(username=username).first()

    def find_user_by_email(self, email: str) -> Optional[Users]:
        return Users.query.filter_by(email=email).first()

    def find_user_by_id(self, user_id: int) -> Optional[Users]:
        return Users.query.get(user_id)

    def update_refresh_token(self, user_id: int, new_token: str) -> None:
        user = self.find_user_by_id(user_id)
        if user:
            user.refresh_token = new_token

    def create_user_with_cat(self, data: dict) -> Users:
        new_user = Users(
            username=data.get('username'),
            email=data.get('email'),
            password_hash=data.get('hashed_password')
        )
        categories_to_add = []
        db.session.add(new_user)
        for cat_data in DEFAULT_CATEGORIES:
            category = Category(
                name=cat_data['name'],
                user=new_user,
                icon=cat_data['icon'],
                mcc_code=cat_data['mcc_code']
            )
            categories_to_add.append(category)
        db.session.add_all(categories_to_add)
        return new_user
