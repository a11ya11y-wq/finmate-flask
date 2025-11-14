from pydantic import ValidationError
from werkzeug.security import check_password_hash, generate_password_hash
from cryptography.fernet import Fernet
from flask import current_app

from .repository import ProfileRepository
from  .schemas import ProfileUpdateSchema, CurrencyUpdateSchema, MonoTokenUpdateSchema, PasswordChangeSchema



class ProfileService:

    def __init__(self):
        self.repo = ProfileRepository()


    def get_user_info(self, user_id):
        user = self.repo.get_user_info(user_id)

        if not user:
            raise ValueError("User not found.")

        return user

    def update_user(self, user_id, data):
        user = self.get_user_info(user_id)

        try:
            validated_data = ProfileUpdateSchema.model_validate(data)
        except ValidationError as e:
            raise ValueError(e.errors())

        payload = validated_data.model_dump(exclude_unset=True)

        if not payload:
            raise ValueError("No valid fields to update.")

        updated_user = self.repo.update_user(user, payload)

        return updated_user


    def delete_user(self, user_id):
        user_to_delete = self.repo.get_user_info(user_id)

        if not user_to_delete:
            raise ValueError(f"User with id {user_id} not found.")

        self.repo.delete_user(user_to_delete)

        return True


    def change_password(self, user_id, data):
        try:
            validated_data = PasswordChangeSchema.model_validate(data)
        except ValidationError as e:
            raise ValueError(e.errors())

        payload = validated_data.model_dump()
        new_password = validated_data.new_password
        old_password = validated_data.old_password
        confirm_password = validated_data.confirm_password

        if new_password == old_password:
            raise ValueError("New password cannot be the same as the old password.")

        if new_password != confirm_password:
            raise ValueError("New password and confirmation do not match.")

        user_obj = self.get_user_info(user_id)

        if not user_obj:
            raise ValueError('User not found.')

        if not user_obj.chek_hash_pwd(old_password):
            raise ValueError("Invalid old password.")

        new_hash = generate_password_hash(new_password)

        self.repo.change_password_hash(user_obj, new_hash)

        return True


    def update_currency(self, user_id, data):
        user_obj = self.repo.get_user_info(user_id)

        try:
            validated_data = CurrencyUpdateSchema.model_validate(data)
        except ValidationError as e:
            raise ValueError(e.errors())

        payload = validated_data.model_dump(exclude_unset=True)

        updated_user = self.repo.update_user(user_id, payload)
        return updated_user


    def update_mono_token(self, user_id, data):
        user_obj = self.repo.get_user_info(user_id)

        try:
            validated_data = MonoTokenUpdateSchema.model_validate(data)
        except ValidationError as e:
            raise ValueError(e.errors())

        try:
            key = current_app.config['ENCRYPTION_KEY']
            cipher_suite = Fernet(key)

            raw_token_bytes = validated_data.token.encode('utf-8')

            encrypted_token = cipher_suite.encrypt(raw_token_bytes)

        except Exception as e:
            raise Exception(f"Token encryption failed: {e}")

        payload = {
            "monobank_api_token": encrypted_token
        }

        updated_user = self.repo.update_user(user_obj, payload)
        return updated_user



