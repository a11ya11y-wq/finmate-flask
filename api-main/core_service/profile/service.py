import logging
from decimal import Decimal

from cryptography.fernet import Fernet
from flask import current_app
from werkzeug.security import generate_password_hash

from core_service.constants import ALLOWED_AVATARS
from core_service.exceptions import ResourceNotFound, BusinessLogicError, AuthenticationError
from core_service.models.user_model import Users
from core_service.uow import UnitOfWork
from core_service.utils.caching import invalidate_cache, redis_cache
from .schemas import ProfileUpdateSchema, MonoTokenUpdateSchema, PasswordChangeSchema

logger = logging.getLogger(__name__)


def profile_key_builder(self, user_id):
    return f"profile:{user_id}"


class ProfileService:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def _get_user_or_404(self, user_id: int) -> Users:
        user = self.uow.profile.get_user_info(user_id)

        if not user:
            logger.warning(f"User entity not found for user_id: {user_id}")
            raise ResourceNotFound("User not found.")

        return user

    @redis_cache(ttl=3600, key_builder=profile_key_builder)
    def get_user_data(self, user_id: int) -> dict:
        user = self._get_user_or_404(user_id)
        return user.to_dict()

    def update_user(self, user_id: int, data: dict) -> Users:

        validated_data = ProfileUpdateSchema.model_validate(data)
        payload = validated_data.model_dump(exclude_unset=True, exclude_none=True)
        if not payload:
            raise BusinessLogicError("No valid fields to update.")

        user = self._get_user_or_404(user_id)

        if 'username' in payload and payload['username'] == user.username:
            payload.pop('username')

        if 'avatar' in payload:
            if payload['avatar'] not in ALLOWED_AVATARS:
                logger.warning(f"User {user_id} attempted to set invalid avatar: {payload['avatar']}")
                raise BusinessLogicError("Invalid avatar selection.")

        if 'username' in payload:
            existing = self.uow.profile.get_by_username(payload['username'])
            if existing:
                logger.warning(
                    f"User {user_id} attempted to change username to an already taken one: {payload['username']}")
                raise BusinessLogicError("Username already taken.")

        if not payload:
            logger.info(f"User {user_id} update called with no actual changes.")
            raise BusinessLogicError("No valid fields to update.")

        updated_user = self.uow.profile.update_user(user, payload)

        self._clear_related_caches(user_id)
        logger.info(f"User {user_id} profile updated.")

        return updated_user

    def delete_user(self, user_id: int) -> bool:
        user_to_delete = self._get_user_or_404(user_id)
        self.uow.profile.delete_user(user_to_delete)

        self._clear_related_caches(user_id)
        self.uow.on_commit(lambda: invalidate_cache(f"categories:{user_id}"))
        self.uow.on_commit(lambda: invalidate_cache(f"dashboard:{user_id}:*"))
        logger.info(f"User {user_id} deleted.")
 
        return True

    def change_password(self, user_id: int, data: dict) -> bool:

        validated_data = PasswordChangeSchema.model_validate(data)

        new_password = validated_data.new_password
        old_password = validated_data.old_password

        new_hash = generate_password_hash(new_password)

        user_obj = self._get_user_or_404(user_id)

        if not user_obj.chek_hash_pwd(old_password):
            logger.warning(f"User {user_id} provided invalid old password for password change.")
            raise AuthenticationError("Invalid old password.")

        self.uow.profile.change_password_hash(user_obj, new_hash)

        self._clear_related_caches(user_id)
        logger.info(f"User {user_id} changed password.")

        return True

    def update_mono_token(self, user_id: int, data: dict) -> Users:

        validated_data = MonoTokenUpdateSchema.model_validate(data)
        try:
            key = current_app.config['ENCRYPTION_KEY']
            cipher_suite = Fernet(key)
            raw_token_bytes = validated_data.token.encode('utf-8')
            encrypted_token = cipher_suite.encrypt(raw_token_bytes)

        except Exception as e:
            logger.exception(f"Token encryption failed for user {user_id}")
            raise Exception("Server error: Could not encrypt token. Please try again.")
        payload = {
            "monobank_api_token": encrypted_token
        }
        user_obj = self._get_user_or_404(user_id)
        updated_user = self.uow.profile.update_user(user_obj, payload)

        self._clear_related_caches(user_id)
        logger.info(f"User {user_id} updated Monobank token.")

        return updated_user

    def delete_mono_token(self, user_id: int) -> bool:

        user_obj = self._get_user_or_404(user_id)
        self.uow.profile.delete_monobank_token(user_obj)

        self._clear_related_caches(user_id)
        logger.info(f"User {user_id} deleted Monobank token.")

        return True

    def recalculate_initial_point(self, user_id: int) -> Decimal:
        user_obj = self._get_user_or_404(user_id)
        real_balance = Decimal(user_obj.last_real_balance or 0)
        current_mono_sum = Decimal(self.uow.transactions.get_current_balance_mono(user_id) or 0)

        new_initial = real_balance - current_mono_sum

        self.uow.profile.setup_initial_balance(user_obj, new_initial)

        self.uow.on_commit(lambda: invalidate_cache(f"dashboard:{user_id}:*"))
        self._clear_related_caches(user_id)
        
        logger.info(f"User {user_id}: Initial point recalculated to {new_initial}")
        return Decimal(new_initial)

    def _clear_related_caches(self, user_id: int):
        self.uow.on_commit(lambda: invalidate_cache(f"profile:{user_id}"))
