from werkzeug.security import check_password_hash, generate_password_hash
from flask_jwt_extended import create_access_token
from datetime import timedelta
from .repository import AuthRepository


class AuthService:

    def __init__(self):
        self.repo = AuthRepository()

    def login_user(self, email, password):
        user = self.repo.find_user_by_email(email)

        if not user or check_password_hash(user.password_hash, password):
            raise ValueError("Invalid email or password.")

        access_token = create_access_token(
            identity=str(user.id),
            expires_delta=timedelta(hours=1)
        )
        return access_token


    def create_user(self, data):

        if not data.get('password'):
            raise ValueError('Password is required field')
        if not data.get('username'):
            raise ValueError('Username is required field')
        if not data.get('email'):
            raise ValueError('Email is required field')

        hashed_password = generate_password_hash(data.get('password'))
        email = data.get('email')
        username = data.get('username')

        new_user = self.repo.create_user_with_cat(
            username=username,
            email=email,
            hashed_password=hashed_password
        )

        return new_user
