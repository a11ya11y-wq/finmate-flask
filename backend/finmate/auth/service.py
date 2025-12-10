from datetime import timedelta

from werkzeug.security import check_password_hash, generate_password_hash
from flask_jwt_extended import create_access_token

from .repository import AuthRepository
from .schemas import LoginSchema, RegisterSchema
from backend.finmate.exceptions import ConflictError, AuthenticationError


class AuthService:

    def __init__(self):
        self.repo = AuthRepository()

    def login_user(self, data):

        validated_data = LoginSchema.model_validate(data)

        user = self.repo.find_user_by_email(validated_data.email)

        if not user or not check_password_hash(user.password_hash, validated_data.password):
            raise AuthenticationError("Invalid email or password.")

        access_token = create_access_token(
            identity=str(user.id),
            expires_delta=timedelta(hours=1)
        )
        return access_token


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
