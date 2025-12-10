from pydantic import ValidationError
from werkzeug.security import check_password_hash, generate_password_hash
from cryptography.fernet import Fernet
from flask import current_app

from .repository import ProfileRepository
from  .schemas import ProfileUpdateSchema, MonoTokenUpdateSchema, PasswordChangeSchema
from backend.finmate.exceptions import ResourceNotFound, BusinessLogicError, AuthenticationError



class ProfileService:

    def __init__(self):
        self.repo = ProfileRepository()


    def get_user_info(self, user_id):
        user = self.repo.get_user_info(user_id)

        if not user:
            raise ResourceNotFound("User not found.")

        return user

    def update_user(self, user_id, data):
        user = self.get_user_info(user_id)

        validated_data = ProfileUpdateSchema.model_validate(data)

        payload = validated_data.model_dump(exclude_unset=True)

        if not payload:
            raise BusinessLogicError("No valid fields to update.")

        updated_user = self.repo.update_user(user, payload)

        return updated_user


    def delete_user(self, user_id):
        user_to_delete = self.get_user_info(user_id)


        self.repo.delete_user(user_to_delete)

        return True


    def change_password(self, user_id, data):

        validated_data = PasswordChangeSchema.model_validate(data)

        new_password = validated_data.new_password
        old_password = validated_data.old_password

        user_obj = self.get_user_info(user_id)

        if not user_obj.chek_hash_pwd(old_password):
            raise AuthenticationError("Invalid old password.")

        new_hash = generate_password_hash(new_password)

        self.repo.change_password_hash(user_obj, new_hash)

        return True


    def update_mono_token(self, user_id, data):
        user_obj = self.get_user_info(user_id)

        validated_data = MonoTokenUpdateSchema.model_validate(data)

        try:
            key = current_app.config['ENCRYPTION_KEY']
            cipher_suite = Fernet(key)

            raw_token_bytes = validated_data.token.encode('utf-8')

            encrypted_token = cipher_suite.encrypt(raw_token_bytes)

        except Exception as e: #TODO: Ловити конкретніші помилки з Фернет
            raise Exception(f"Token encryption failed: {e}")

        payload = {
            "monobank_api_token": encrypted_token
        }

        updated_user = self.repo.update_user(user_obj, payload)
        return updated_user


    def delete_mono_token(self, user_id):
        user_obj = self.get_user_info(user_id)
        self.repo.delete_monobank_token(user_obj)
        return True



