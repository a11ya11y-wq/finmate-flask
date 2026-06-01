import pytest
from unittest.mock import MagicMock
from datetime import datetime, timezone, timedelta
from pydantic import ValidationError

from core_service.exceptions import ConflictError, AuthenticationError
from core_service.auth.service import AuthService 
from core_service.models.user_model import Users


@pytest.fixture
def auth_uow():
    mock_uow = MagicMock()
    return mock_uow

@pytest.fixture
def auth_service(auth_uow, mocker):
    service = AuthService(auth_uow)

    mocker.patch.object(AuthService, 'redis', new_callable=MagicMock)
    return service

VALID_LOGIN_DATA = {"email": "test@example.com", "password": "password123"}
VALID_REGISTER_DATA = {"username": "testuser", "email": "test@example.com", "password": "password123", "confirm_password": "password123"}

class TestLoginUser:

    @pytest.mark.parametrize("remember_me, expected_days", [
        (False, 1),
        (True, 30)
    ])
    def test_login_user_success(self, auth_service, auth_uow, mocker, remember_me, expected_days):
        """Successful login with and without remember_me"""
        
        mock_user = MagicMock(spec=Users)
        mock_user.id = 142
        mock_user.password_hash = "hashed_pass"
        auth_uow.auth.find_user_by_email.return_value = mock_user

        mocker.patch("core_service.auth.service.check_password_hash", return_value=True)
        mock_create_access = mocker.patch("core_service.auth.service.create_access_token", return_value="access_jwt")
        mock_create_refresh = mocker.patch("core_service.auth.service.create_refresh_token", return_value="refresh_jwt")

        access_token, refresh_token, expires = auth_service.login_user(VALID_LOGIN_DATA, remember_me=remember_me)

        assert access_token == "access_jwt"
        assert refresh_token == "refresh_jwt"
        assert expires == timedelta(days=expected_days)

        auth_uow.auth.find_user_by_email.assert_called_once_with("test@example.com")
        mock_create_access.assert_called_once_with(identity="142", expires_delta=timedelta(minutes=30))
        mock_create_refresh.assert_called_once_with(
            identity="142", 
            expires_delta=timedelta(days=expected_days), 
            additional_claims={"remember": remember_me}
        )
        auth_uow.auth.update_refresh_token.assert_called_once_with(142, "refresh_jwt")

    def test_login_user_not_found(self, auth_service, auth_uow):
        """AuthenticationError if user email is not in DB"""
        auth_uow.auth.find_user_by_email.return_value = None

        with pytest.raises(AuthenticationError, match="Invalid email or password."):
            auth_service.login_user(VALID_LOGIN_DATA)

    def test_login_user_wrong_password(self, auth_service, auth_uow, mocker):
        """AuthenticationError if password hash doesn't match"""
        auth_uow.auth.find_user_by_email.return_value = MagicMock(password_hash="real_hash")
        mocker.patch("core_service.auth.service.check_password_hash", return_value=False)

        with pytest.raises(AuthenticationError, match="Invalid email or password."):
            auth_service.login_user(VALID_LOGIN_DATA)


class TestRefreshAccessToken:

    @pytest.mark.parametrize("is_remember_me, expected_days", [
        (False, 1),
        (True, 30)
    ])
    def test_refresh_token_success(self, auth_service, auth_uow, mocker, is_remember_me, expected_days):
        """Successfully issue new pair of tokens"""
        
        mock_payload = {"sub": 142, "remember": is_remember_me}
        mocker.patch("core_service.auth.service.decode_token", return_value=mock_payload)

        mock_user = MagicMock(spec=Users)
        mock_user.id = 142
        mock_user.refresh_token = "old_valid_refresh_token"
        auth_uow.auth.find_user_by_id.return_value = mock_user

        mocker.patch("core_service.auth.service.create_access_token", return_value="new_access")
        mocker.patch("core_service.auth.service.create_refresh_token", return_value="new_refresh")

        acc, ref, exp = auth_service.refresh_access_token("old_valid_refresh_token")

        assert acc == "new_access"
        assert ref == "new_refresh"
        assert exp == timedelta(days=expected_days)
        auth_uow.auth.update_refresh_token.assert_called_once_with(142, "new_refresh")

    def test_refresh_token_user_not_found(self, auth_service, auth_uow, mocker):
        """Fail if user was deleted but token is still alive"""
        mocker.patch("core_service.auth.service.decode_token", return_value={"sub": 142})
        auth_uow.auth.find_user_by_id.return_value = None

        with pytest.raises(AuthenticationError, match="User no longer exists"):
            auth_service.refresh_access_token("some_token")

    def test_refresh_token_mismatch(self, auth_service, auth_uow, mocker):
        """Fail if token doesn't match the one in DB (e.g., family token revocation)"""
        mocker.patch("core_service.auth.service.decode_token", return_value={"sub": 142})
        
        mock_user = MagicMock(refresh_token="token_in_db")
        auth_uow.auth.find_user_by_id.return_value = mock_user

        with pytest.raises(AuthenticationError, match="Token revoked or replaced"):
            auth_service.refresh_access_token("different_token_from_client")


class TestCreateUser:

    def test_create_user_success(self, auth_service, auth_uow, mocker):
        """Successfully register a new user"""
        
        auth_uow.auth.find_user_by_email.return_value = None
        auth_uow.auth.find_user_by_name.return_value = None
        
        mocker.patch("core_service.auth.service.generate_password_hash", return_value="hashed_123")
        
        mock_created_user = MagicMock(id=99)
        auth_uow.auth.create_user_with_cat.return_value = mock_created_user

        result = auth_service.create_user(VALID_REGISTER_DATA)

        assert result.id == 99
        auth_uow.auth.create_user_with_cat.assert_called_once_with({
            "username": "testuser",
            "email": "test@example.com",
            "hashed_password": "hashed_123"
        })
        auth_uow.flush.assert_called_once()

    def test_create_user_email_conflict(self, auth_service, auth_uow):
        """ConflictError if email already exists"""
        auth_uow.auth.find_user_by_email.return_value = MagicMock()

        with pytest.raises(ConflictError, match="Email already registered."):
            auth_service.create_user(VALID_REGISTER_DATA)
            
        auth_uow.auth.create_user_with_cat.assert_not_called()

    def test_create_user_username_conflict(self, auth_service, auth_uow):
        """ConflictError if username already exists"""
        auth_uow.auth.find_user_by_email.return_value = None
        auth_uow.auth.find_user_by_name.return_value = MagicMock()

        with pytest.raises(ConflictError, match="Username already registered"):
            auth_service.create_user(VALID_REGISTER_DATA)


class TestLogoutUser:

    def test_logout_user_success_with_redis(self, auth_service, auth_uow, mocker):
        """Successfully wipe refresh token and blacklist access token"""
        
        current_time = datetime.now(timezone.utc).timestamp()
        exp_time = current_time + 1000 
        
        mock_payload = {
            "jti": "jwt-id-123",
            "exp": exp_time,
            "sub": 142
        }
        mocker.patch("core_service.auth.service.decode_token", return_value=mock_payload)

        auth_service.logout_user("valid_access_token")

        auth_uow.auth.update_refresh_token.assert_called_once_with(142, None)
        
        args, kwargs = auth_service.redis.setex.call_args
        assert args[0] == "auth:blacklist:jwt-id-123"
        assert args[1] > 0  # ttl
        assert args[2] == "revoked"

    def test_logout_user_expired_token(self, auth_service, auth_uow, mocker):
        """If access token is already expired, we don't need to put it in Redis"""
        
        current_time = datetime.now(timezone.utc).timestamp()
        exp_time = current_time - 500 
        
        mock_payload = {"jti": "jwt-id-123", "exp": exp_time, "sub": 142}
        mocker.patch("core_service.auth.service.decode_token", return_value=mock_payload)

        auth_service.logout_user("expired_access_token")

        auth_uow.auth.update_refresh_token.assert_called_once_with(142, None)
        auth_service.redis.setex.assert_not_called() 