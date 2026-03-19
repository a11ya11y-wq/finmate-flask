import logging
from decimal import Decimal

from cryptography.fernet import Fernet
from flask import current_app
from werkzeug.security import generate_password_hash

from finmate.constants import ALLOWED_AVATARS
from finmate.exceptions import ResourceNotFound, BusinessLogicError, AuthenticationError
from finmate.models.user_model import Users
from finmate.uow import UnitOfWork
from finmate.utils.caching import invalidate_cache, redis_cache
from .schemas import ProfileUpdateSchema, MonoTokenUpdateSchema, PasswordChangeSchema

logger = logging.getLogger(__name__)


def profile_key_builder(self, user_id):
    return f"profile:{user_id}"


class ProfileService:

    def _get_user_or_404(self, uow: UnitOfWork, user_id: int) -> Users:
        user = uow.profile.get_user_info(user_id)

        if not user:
            logger.warning(f"User entity not found for user_id: {user_id}")
            raise ResourceNotFound("User not found.")

        return user

    def get_user_entity(self, user_id: int) -> Users:
        with UnitOfWork() as uow:
            return self._get_user_or_404(uow, user_id)

    @redis_cache(ttl=3600, key_builder=profile_key_builder)
    def get_user_data(self, user_id: int) -> dict:
        user = self.get_user_entity(user_id)
        return user.to_dict()

    def update_user(self, user_id: int, data: dict) -> Users:

        validated_data = ProfileUpdateSchema.model_validate(data)
        payload = validated_data.model_dump(exclude_unset=True)
        if not payload:
            raise BusinessLogicError("No valid fields to update.")

        with UnitOfWork() as uow:

            user = self._get_user_or_404(uow, user_id)

            if 'username' in payload and payload['username'] == user.username:
                payload.pop('username')

            if 'avatar' in payload:
                if payload['avatar'] not in ALLOWED_AVATARS:
                    logger.warning(f"User {user_id} attempted to set invalid avatar: {payload['avatar']}")
                    raise BusinessLogicError("Invalid avatar selection.")

            if 'username' in payload:
                existing = uow.profile.get_by_username(payload['username'])
                if existing:
                    logger.warning(
                        f"User {user_id} attempted to change username to an already taken one: {payload['username']}")
                    raise BusinessLogicError("Username already taken.")

            updated_user = uow.profile.update_user(user, payload)
            uow.commit()

        try:
            self._clear_related_caches(user_id)
            logger.info(f"User {user_id} profile updated.")
        except Exception as e:
            logger.error(f"Post-commit action failed: {e}")
        return updated_user

    def delete_user(self, user_id: int) -> bool:

        with UnitOfWork() as uow:
            user_to_delete = self._get_user_or_404(uow, user_id)
            uow.profile.delete_user(user_to_delete)
            uow.commit()

        try:
            self._clear_related_caches(user_id)
            invalidate_cache(f"categories:{user_id}")
            invalidate_cache(f"dashboard:{user_id}:*")
            logger.info(f"User {user_id} deleted.")
        except Exception as e:
            logger.error(f"Post-commit action failed: {e}")
        return True

    def change_password(self, user_id: int, data: dict) -> bool:

        validated_data = PasswordChangeSchema.model_validate(data)

        new_password = validated_data.new_password
        old_password = validated_data.old_password

        new_hash = generate_password_hash(new_password)

        with UnitOfWork() as uow:

            user_obj = self._get_user_or_404(uow, user_id)

            if not user_obj.chek_hash_pwd(old_password):
                logger.warning(f"User {user_id} provided invalid old password for password change.")
                raise AuthenticationError("Invalid old password.")

            uow.profile.change_password_hash(user_obj, new_hash)
            uow.commit()

        try:
            self._clear_related_caches(user_id)
            logger.info(f"User {user_id} changed password.")
        except Exception as e:
            logger.error(f"Post-commit action failed: {e}")
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

        with UnitOfWork() as uow:
            user_obj = self._get_user_or_404(uow, user_id)
            updated_user = uow.profile.update_user(user_obj, payload)
            uow.commit()

        try:
            self._clear_related_caches(user_id)
            logger.info(f"User {user_id} updated Monobank token.")
        except Exception as e:
            logger.error(f"Post-commit action failed: {e}")
        return updated_user

    def delete_mono_token(self, user_id: int) -> bool:

        with UnitOfWork() as uow:
            user_obj = self._get_user_or_404(uow, user_id)
            uow.profile.delete_monobank_token(user_obj)
            uow.commit()
        try:
            self._clear_related_caches(user_id)
            logger.info(f"User {user_id} deleted Monobank token.")
        except Exception as e:
            logger.error(f"Post-commit action failed: {e}")
        return True

    def recalculate_initial_point(self, uow: UnitOfWork, user_id: int) -> Decimal:
        user_obj = self._get_user_or_404(uow, user_id)
        real_balance = Decimal(user_obj.last_real_balance or 0)
        current_mono_sum = Decimal(uow.transactions.get_current_balance_mono(user_id) or 0)

        new_initial = real_balance - current_mono_sum
        print(real_balance, current_mono_sum, "new", new_initial)
        uow.profile.setup_initial_balance(user_obj, new_initial)
        try:
            invalidate_cache(f"dashboard:{user_id}:*")
            self._clear_related_caches(user_id)
        except Exception as e:
            logger.error(f"Post-commit action failed: {e}")
        logger.info(f"User {user_id}: Initial point recalculated to {new_initial}")
        return Decimal(new_initial)

    @staticmethod
    def _clear_related_caches(user_id):
        invalidate_cache(f"profile:{user_id}")
