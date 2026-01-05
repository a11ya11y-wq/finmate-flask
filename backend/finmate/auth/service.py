from datetime import timedelta, datetime, timezone

from werkzeug.security import check_password_hash, generate_password_hash
from flask_jwt_extended import create_access_token, create_refresh_token, decode_token

from .repository import AuthRepository
from .schemas import LoginSchema, RegisterSchema
from backend.finmate.exceptions import ConflictError, AuthenticationError
from backend.finmate import extensions

class AuthService:

    def __init__(self):
        self.repo = AuthRepository()

    @property
    def redis(self):
        return extensions.redis_client

    def login_user(self, data, remember_me=False):

        validated_data = LoginSchema.model_validate(data)

        user = self.repo.find_user_by_email(validated_data.email)

        if not user or not check_password_hash(user.password_hash, validated_data.password):
            raise AuthenticationError("Invalid email or password.")

        access_token = create_access_token(
            identity=str(user.id),
            expires_delta=timedelta(minutes=30)
        )
        if remember_me:
            refresh_expires = timedelta(days=30)
        else:
            refresh_expires = timedelta(days=1)

        refresh_token = create_refresh_token(
            identity=str(user.id),
            expires_delta=refresh_expires,
            additional_claims={"remember": remember_me}
        )

        self.repo.update_refresh_token(user.id, refresh_token)

        return access_token, refresh_token, refresh_expires


    def refresh_access_token(self, refresh_token):
        try:
            payload = decode_token(refresh_token)

            user_id = payload.get("sub")
            user = self.repo.find_user_by_id(user_id)
            is_remember_me = payload.get("remember", False)

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

            self.repo.update_refresh_token(user_id, new_refresh_token)

            return new_access_token, new_refresh_token, refresh_expires

        except Exception as e:
            raise AuthenticationError("Invalid refresh token")


    def create_user(self, data):

        validated_data = RegisterSchema.model_validate(data)

        if self.repo.find_user_by_email(validated_data.email):
            raise ConflictError("Email already registered.")

        if self.repo.find_user_by_name(validated_data.username):
            raise ConflictError("Username already registered")

        hashed_password = generate_password_hash(validated_data.password)

        user_data_payload = {
            "username": validated_data.username,
            "email": validated_data.email,
            "hashed_password": hashed_password
        }

        new_user = self.repo.create_user_with_cat(user_data_payload)
        return new_user


    def logout_user(self, access_token):
        try:
            payload = decode_token(access_token)
            jti = payload.get("jti")
            exp_timestamp = payload.get("exp")
            user_id = payload.get("sub")

            self.repo.update_refresh_token(user_id, None)

            current_timestamp = datetime.now(timezone.utc).timestamp()
            ttl = int(exp_timestamp - current_timestamp)


            if ttl > 0:
                self.redis.setex(f"auth:blacklist:{jti}", ttl, "revoked")

        except Exception as e:
            print(f"!!! REDIS ERROR !!!: {e}")