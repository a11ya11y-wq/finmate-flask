from werkzeug.security import generate_password_hash
from cryptography.fernet import Fernet
from flask import current_app

from .repository import ProfileRepository
from  .schemas import ProfileUpdateSchema, MonoTokenUpdateSchema, PasswordChangeSchema
from backend.finmate.exceptions import ResourceNotFound, BusinessLogicError, AuthenticationError
from backend.finmate.utils.caching import invalidate_cache, redis_cache
from backend.finmate.constants import ALLOWED_AVATARS


def profile_key_builder(self, user_id):
    return f"profile:{user_id}"


class ProfileService:

    def __init__(self):
        self.repo = ProfileRepository()


    def get_user_entity(self, user_id):
        user = self.repo.get_user_info(user_id)

        if not user:
            raise ResourceNotFound("User not found.")

        return user


    @redis_cache(ttl=3600, key_builder=profile_key_builder)
    def get_user_data(self, user_id):
        user = self.get_user_entity(user_id)
        return user.to_dict()


    def update_user(self, user_id, data):
        user = self.get_user_entity(user_id)

        validated_data = ProfileUpdateSchema.model_validate(data)

        payload = validated_data.model_dump(exclude_unset=True)

        if 'username' in payload and payload['username'] == user.username:
            payload.pop('username')

        if not payload:
            raise BusinessLogicError("No valid fields to update.")

        if 'username' in payload:
            existing = self.repo.get_by_username(payload['username'])
            if existing:
                raise BusinessLogicError("Username already taken.")

        if 'avatar' in payload:
            if payload['avatar'] not in ALLOWED_AVATARS:
                raise BusinessLogicError("Invalid avatar selection.")

        updated_user = self.repo.update_user(user, payload)

        self._clear_related_caches(user_id)
        return updated_user


    def delete_user(self, user_id):
        user_to_delete = self.get_user_entity(user_id)


        self.repo.delete_user(user_to_delete)

        self._clear_related_caches(user_id)
        return True


    def change_password(self, user_id, data):

        validated_data = PasswordChangeSchema.model_validate(data)

        new_password = validated_data.new_password
        old_password = validated_data.old_password

        user_obj = self.get_user_entity(user_id)

        if not user_obj.chek_hash_pwd(old_password):
            raise AuthenticationError("Invalid old password.")

        new_hash = generate_password_hash(new_password)

        self.repo.change_password_hash(user_obj, new_hash)

        self._clear_related_caches(user_id)
        return True


    def update_mono_token(self, user_id, data):
        user_obj = self.get_user_entity(user_id)

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

        self._clear_related_caches(user_id)
        return updated_user


    def delete_mono_token(self, user_id):
        user_obj = self.get_user_entity(user_id)
        self.repo.delete_monobank_token(user_obj)

        self._clear_related_caches(user_id)
        return True


    @staticmethod
    def _clear_related_caches(user_id):
        invalidate_cache(f"profile:{user_id}")



