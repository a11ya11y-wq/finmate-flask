import logging
from datetime import timedelta, datetime, timezone

from flask_jwt_extended import create_access_token, create_refresh_token, decode_token
from werkzeug.security import check_password_hash, generate_password_hash

from core_service import extensions
from core_service.exceptions import ConflictError, AuthenticationError
from core_service.models.user_model import Users
from core_service.uow import UnitOfWork
from .schemas import LoginSchema, RegisterSchema

logger = logging.getLogger(__name__)


class AuthService:

    @property
    def redis(self):
        return extensions.redis_client

    def login_user(self, data: int, remember_me: bool = False) -> tuple:

        validated_data = LoginSchema.model_validate(data)

        with UnitOfWork() as uow:
            user = uow.auth.find_user_by_email(validated_data.email)

            if not user or not check_password_hash(user.password_hash, validated_data.password):
                logger.warning(f"Failed login attempt for email: {validated_data.email}")
                raise AuthenticationError("Invalid email or password.")
            user_id = user.id

            access_token = create_access_token(
                identity=str(user_id),
                expires_delta=timedelta(minutes=30)
            )
            if remember_me:
                refresh_expires = timedelta(days=30)
            else:
                refresh_expires = timedelta(days=1)

            refresh_token = create_refresh_token(
                identity=str(user_id),
                expires_delta=refresh_expires,
                additional_claims={"remember": remember_me}
            )

            uow.auth.update_refresh_token(user_id, refresh_token)
            uow.commit()

        logger.info(f"User {user_id} logged in successfully.")
        return access_token, refresh_token, refresh_expires

    def refresh_access_token(self, refresh_token: str) -> tuple:
        try:
            payload = decode_token(refresh_token)
            user_id = payload.get("sub")
            is_remember_me = payload.get("remember", False)

            with UnitOfWork() as uow:
                user = uow.auth.find_user_by_id(user_id)

                if not user:
                    raise AuthenticationError("User no longer exists")

                if user.refresh_token != refresh_token:
                    raise AuthenticationError("Token revoked or replaced")

                if is_remember_me:
                    refresh_expires = timedelta(days=30)
                else:
                    refresh_expires = timedelta(days=1)

                new_access_token = create_access_token(
                    identity=str(user.id),
                    expires_delta=timedelta(minutes=30)
                )

                new_refresh_token = create_refresh_token(
                    identity=str(user.id),
                    expires_delta=refresh_expires,
                    additional_claims={"remember": is_remember_me}
                )

                uow.auth.update_refresh_token(user_id, new_refresh_token)
                uow.commit()

            logger.info(f"Access token refreshed for user {user_id}")
            return new_access_token, new_refresh_token, refresh_expires

        except Exception as e:
            logger.warning(f"Failed to refresh access token: {e}")
            raise AuthenticationError("Invalid refresh token")

    def create_user(self, data: dict) -> Users:

        validated_data = RegisterSchema.model_validate(data)
        hashed_password = generate_password_hash(validated_data.password)

        with UnitOfWork() as uow:
            if uow.auth.find_user_by_email(validated_data.email):
                logger.warning(f"Registration failed: Email {validated_data.email} already exists")
                raise ConflictError("Email already registered.")

            if uow.auth.find_user_by_name(validated_data.username):
                logger.warning(f"Registration failed: Username {validated_data.username} already exists")
                raise ConflictError("Username already registered")

            user_data_payload = {
                "username": validated_data.username,
                "email": validated_data.email,
                "hashed_password": hashed_password
            }

            new_user = uow.auth.create_user_with_cat(user_data_payload)
            uow.commit()

        logger.info(f"New user created with ID: {new_user.id}")
        return new_user

    def logout_user(self, access_token: str) -> None:
        try:
            payload = decode_token(access_token)
            jti = payload.get("jti")
            exp_timestamp = payload.get("exp")
            user_id = payload.get("sub")

            with UnitOfWork() as uow:
                uow.auth.update_refresh_token(user_id, None)
                uow.commit()

            current_timestamp = datetime.now(timezone.utc).timestamp()
            ttl = int(exp_timestamp - current_timestamp)

            if ttl > 0:
                try:
                    self.redis.setex(f"auth:blacklist:{jti}", ttl, "revoked")
                except Exception as e:
                    logger.warning(f"Redis unavailable during logout: {e}")

            logger.info(f"User {user_id} logged out successfully.")
        except Exception as e:
            logger.exception("Error during logout")
