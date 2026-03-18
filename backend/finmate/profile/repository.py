from decimal import Decimal
from typing import Optional

from finmate.extensions import db
from finmate.models import Users


class ProfileRepository:

    def get_user_info(self, user_id: int) -> Optional[Users]:
        return Users.query.get(user_id)

    def get_by_username(self, username: str) -> Users:
        return Users.query.filter_by(username=username).first()

    def update_user(self, user_obj: Users, data: dict) -> Users:
        user_obj.username = data.get('username', user_obj.username)
        user_obj.email = data.get('email', user_obj.email)
        user_obj.currency = data.get('currency', user_obj.currency)
        user_obj.avatar = data.get('avatar', user_obj.avatar)
        if 'monobank_api_token' in data:
            user_obj.monobank_api_token = data.get('monobank_api_token')

        return user_obj

    def delete_monobank_token(self, user_obj: Users) -> None:
        user_obj.monobank_api_token = None

    def delete_user(self, user_obj: Users) -> None:
        db.session.delete(user_obj)

    def change_password_hash(self, user_obj: Users, password_hash: str) -> None:
        user_obj.password_hash = password_hash

    def setup_initial_balance(self, user_obj: Users, initial_balance: Decimal) -> None:
        user_obj.initial_balance = initial_balance

    def update_real_balance(self, user_obj: Users, new_balance: Decimal) -> None:
        user_obj.last_real_balance = new_balance
