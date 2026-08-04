from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import allure
import pytest
from core_service.auth.service import AuthService
from core_service.exceptions import AuthenticationError, ConflictError
from core_service.models.user_model import Users


@pytest.fixture
@allure.title("Mocking Auth Unit of Work")
def auth_uow():
    with allure.step("Initialize MagicMock for Unit of Work"):
        return MagicMock()


@pytest.fixture
@allure.title("Creating AuthService with Mocked Redis")
def auth_service(auth_uow, mocker):
    with allure.step("Create AuthService instance"):
        service = AuthService(auth_uow)
    with allure.step("Patch Redis client with MagicMock"):
        mocker.patch.object(AuthService, "redis", new_callable=MagicMock)
    return service


VALID_LOGIN_DATA = {"email": "test@example.com", "password": "password123"}
VALID_REGISTER_DATA = {
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123",
    "confirm_password": "password123",
}


@allure.feature("Authentication")
@allure.story("Login User")
class TestLoginUser:

    @allure.title("Successful login (remember_me={remember_me})")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.parametrize("remember_me, expected_days", [(False, 1), (True, 30)])
    def test_login_user_success(
        self, auth_service, auth_uow, mocker, remember_me, expected_days
    ):
        with allure.step("Arrange: Prepare mock user and token generation"):
            mock_user = MagicMock(spec=Users)
            mock_user.id = 142
            mock_user.email = "test@example.com"
            mock_user.password_hash = "hashed_pass"
            auth_uow.auth.find_user_by_email.return_value = mock_user

            mocker.patch(
                "core_service.auth.service.check_password_hash", return_value=True
            )
            mock_create_access = mocker.patch(
                "core_service.auth.service.create_access_token",
                return_value="access_jwt",
            )
            mock_create_refresh = mocker.patch(
                "core_service.auth.service.create_refresh_token",
                return_value="refresh_jwt",
            )

        with allure.step("Act: Call login_user service method"):
            access_token, refresh_token, expires = auth_service.login_user(
                VALID_LOGIN_DATA, remember_me=remember_me
            )

        with allure.step("Assert: Verify returned tokens and expiration"):
            assert access_token == "access_jwt"
            assert refresh_token == "refresh_jwt"
            assert expires == timedelta(days=expected_days)

        with allure.step("Assert: Verify UOW and token creation calls"):
            auth_uow.auth.find_user_by_email.assert_called_once_with("test@example.com")
            mock_create_access.assert_called_once_with(
                identity="142",
                expires_delta=timedelta(minutes=30),
                additional_claims={"email": "test@example.com"},
            )
            mock_create_refresh.assert_called_once_with(
                identity="142",
                expires_delta=timedelta(days=expected_days),
                additional_claims={"remember": remember_me},
            )
            auth_uow.auth.update_refresh_token.assert_called_once_with(
                142, "refresh_jwt"
            )

    @allure.title("Login fails when user is not found in DB")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_login_user_not_found(self, auth_service, auth_uow):
        with allure.step("Arrange: Mock UOW to return None for user email"):
            auth_uow.auth.find_user_by_email.return_value = None

        with allure.step("Act & Assert: Expect AuthenticationError"):
            with pytest.raises(AuthenticationError, match="Invalid email or password."):
                auth_service.login_user(VALID_LOGIN_DATA)

    @allure.title("Login fails with incorrect password")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_login_user_wrong_password(self, auth_service, auth_uow, mocker):
        with allure.step("Arrange: Mock user and force hash check to fail"):
            auth_uow.auth.find_user_by_email.return_value = MagicMock(
                password_hash="real_hash"
            )
            mocker.patch(
                "core_service.auth.service.check_password_hash", return_value=False
            )

        with allure.step("Act & Assert: Expect AuthenticationError"):
            with pytest.raises(AuthenticationError, match="Invalid email or password."):
                auth_service.login_user(VALID_LOGIN_DATA)

    @allure.title("Login successful for demo user and triggers reset")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_login_user_demo_account(self, auth_service, auth_uow, mocker):
        with allure.step("Arrange: Mock demo user"):
            mock_user = MagicMock(spec=Users)
            mock_user.id = 142
            mock_user.email = "demo@test.com"
            mock_user.password_hash = "hashed_pass"
            auth_uow.auth.find_user_by_email.return_value = mock_user

            mocker.patch(
                "core_service.auth.service.check_password_hash", return_value=True
            )
            mocker.patch(
                "core_service.auth.service.create_access_token",
                return_value="access_jwt",
            )
            mocker.patch(
                "core_service.auth.service.create_refresh_token",
                return_value="refresh_jwt",
            )
            mock_reset = mocker.patch.object(auth_service, "_reset_demo_account")

        with allure.step("Act: Call login_user with demo email"):
            auth_service.login_user({"email": "demo@test.com", "password": "password123"})
            
        with allure.step("Assert: Verify reset was triggered"):
            mock_reset.assert_called_once_with(142)


@allure.feature("Authentication")
@allure.story("Refresh Token")
class TestRefreshAccessToken:

    @allure.title("Successfully refresh tokens (remember_me={is_remember_me})")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.parametrize("is_remember_me, expected_days", [(False, 1), (True, 30)])
    def test_refresh_token_success(
        self, auth_service, auth_uow, mocker, is_remember_me, expected_days
    ):
        with allure.step("Arrange: Mock decoded token and active user"):
            mock_payload = {"sub": 142, "remember": is_remember_me}
            mocker.patch(
                "core_service.auth.service.decode_token", return_value=mock_payload
            )

            mock_user = MagicMock(spec=Users)
            mock_user.id = 142
            mock_user.refresh_token = "old_valid_refresh_token"
            auth_uow.auth.find_user_by_id.return_value = mock_user

            mocker.patch(
                "core_service.auth.service.create_access_token",
                return_value="new_access",
            )
            mocker.patch(
                "core_service.auth.service.create_refresh_token",
                return_value="new_refresh",
            )

        with allure.step("Act: Call refresh_access_token"):
            acc, ref, exp = auth_service.refresh_access_token("old_valid_refresh_token")

        with allure.step("Assert: Verify new tokens and UOW update call"):
            assert acc == "new_access"
            assert ref == "new_refresh"
            assert exp == timedelta(days=expected_days)
            auth_uow.auth.update_refresh_token.assert_called_once_with(
                142, "new_refresh"
            )

    @allure.title("Refresh fails if user no longer exists")
    @allure.severity(allure.severity_level.NORMAL)
    def test_refresh_token_user_not_found(self, auth_service, auth_uow, mocker):
        with allure.step("Arrange: Mock valid token but missing user in DB"):
            mocker.patch(
                "core_service.auth.service.decode_token", return_value={"sub": 142}
            )
            auth_uow.auth.find_user_by_id.return_value = None

        with allure.step("Act & Assert: Expect AuthenticationError"):
            with pytest.raises(AuthenticationError, match="User no longer exists"):
                auth_service.refresh_access_token("some_token")

    @allure.title("Refresh fails if token does not match DB (revoked/replaced)")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_refresh_token_mismatch(self, auth_service, auth_uow, mocker):
        with allure.step("Arrange: Mock token mismatch between client and DB"):
            mocker.patch(
                "core_service.auth.service.decode_token", return_value={"sub": 142}
            )
            mock_user = MagicMock(refresh_token="token_in_db")
            auth_uow.auth.find_user_by_id.return_value = mock_user

        with allure.step("Act & Assert: Expect AuthenticationError"):
            with pytest.raises(AuthenticationError, match="Token revoked or replaced"):
                auth_service.refresh_access_token("different_token_from_client")


@allure.feature("User Management")
@allure.story("Registration")
class TestCreateUser:

    @allure.title("Successfully register a new user")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_create_user_success(self, auth_service, auth_uow, mocker):
        with allure.step("Arrange: Ensure email/username are free and mock hash"):
            auth_uow.auth.find_user_by_email.return_value = None
            auth_uow.auth.find_user_by_name.return_value = None

            mocker.patch(
                "core_service.auth.service.generate_password_hash",
                return_value="hashed_123",
            )
            mock_created_user = MagicMock(id=99)
            auth_uow.auth.create_user_with_cat.return_value = mock_created_user

        with allure.step("Act: Call create_user"):
            result = auth_service.create_user(VALID_REGISTER_DATA)

        with allure.step("Assert: Verify user creation and DB flush"):
            assert result.id == 99
            auth_uow.auth.create_user_with_cat.assert_called_once_with(
                {
                    "username": "testuser",
                    "email": "test@example.com",
                    "hashed_password": "hashed_123",
                }
            )
            auth_uow.flush.assert_called_once()

    @allure.title("Registration fails due to email conflict")
    @allure.severity(allure.severity_level.NORMAL)
    def test_create_user_email_conflict(self, auth_service, auth_uow):
        with allure.step("Arrange: Mock existing email in DB"):
            auth_uow.auth.find_user_by_email.return_value = MagicMock()

        with allure.step("Act & Assert: Expect ConflictError"):
            with pytest.raises(ConflictError, match="Email already registered."):
                auth_service.create_user(VALID_REGISTER_DATA)

        with allure.step("Assert: Ensure user was not created"):
            auth_uow.auth.create_user_with_cat.assert_not_called()

    @allure.title("Registration fails due to username conflict")
    @allure.severity(allure.severity_level.NORMAL)
    def test_create_user_username_conflict(self, auth_service, auth_uow):
        with allure.step("Arrange: Mock free email but existing username"):
            auth_uow.auth.find_user_by_email.return_value = None
            auth_uow.auth.find_user_by_name.return_value = MagicMock()

        with allure.step("Act & Assert: Expect ConflictError"):
            with pytest.raises(ConflictError, match="Username already registered"):
                auth_service.create_user(VALID_REGISTER_DATA)


@allure.feature("Authentication")
@allure.story("Logout User")
class TestLogoutUser:

    @allure.title("Successfully logout user (wipes refresh token, blacklists access)")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_logout_user_success_with_redis(self, auth_service, auth_uow, mocker):
        with allure.step("Arrange: Prepare valid access token payload"):
            current_time = datetime.now(timezone.utc).timestamp()
            exp_time = current_time + 1000

            mock_payload = {"jti": "jwt-id-123", "exp": exp_time, "sub": 142}
            mocker.patch(
                "core_service.auth.service.decode_token", return_value=mock_payload
            )

        with allure.step("Act: Call logout_user"):
            auth_service.logout_user("valid_access_token")

        with allure.step(
            "Assert: Verify refresh token wiped and access token blacklisted in Redis"
        ):
            auth_uow.auth.update_refresh_token.assert_called_once_with(142, None)
            args, kwargs = auth_service.redis.setex.call_args
            assert args[0] == "auth:blacklist:jwt-id-123"
            assert args[1] > 0  # ttl
            assert args[2] == "revoked"

    @allure.title("Logout with already expired token (skips Redis blacklist)")
    @allure.severity(allure.severity_level.NORMAL)
    def test_logout_user_expired_token(self, auth_service, auth_uow, mocker):
        with allure.step("Arrange: Prepare expired access token payload"):
            current_time = datetime.now(timezone.utc).timestamp()
            exp_time = current_time - 500

            mock_payload = {"jti": "jwt-id-123", "exp": exp_time, "sub": 142}
            mocker.patch(
                "core_service.auth.service.decode_token", return_value=mock_payload
            )

        with allure.step("Act: Call logout_user"):
            auth_service.logout_user("expired_access_token")

        with allure.step("Assert: Verify refresh token wiped but Redis was not called"):
            auth_uow.auth.update_refresh_token.assert_called_once_with(142, None)
            auth_service.redis.setex.assert_not_called()


@allure.feature("Authentication")
@allure.story("Demo Account")
class TestDemoAccountReset:
    
    @allure.title("Successfully reset demo account")
    def test_reset_demo_account_success(self, auth_service, auth_uow, mocker):
        with allure.step("Act: Call _reset_demo_account"):
            auth_service._reset_demo_account(142)
            
        with allure.step("Assert: SQL executed and redis cleared"):
            auth_uow.auth.execute_raw_sql.assert_called_once()
            assert len(auth_uow.auth.execute_raw_sql.call_args[0][0]) > 0
            auth_uow.flush.assert_called_once()
            auth_service.redis.delete.assert_called_once()
            
            deleted_keys = auth_service.redis.delete.call_args[0]
            assert "profile:142" in deleted_keys
            assert len(deleted_keys) == 7

    @allure.title("Reset demo account handles exceptions gracefully")
    def test_reset_demo_account_exception(self, auth_service, auth_uow, mocker):
        with allure.step("Arrange: Force an exception during sql execution"):
            auth_uow.auth.execute_raw_sql.side_effect = Exception("DB Error")
            mock_logger = mocker.patch("core_service.auth.service.logger.error")
            
        with allure.step("Act: Call _reset_demo_account"):
            auth_service._reset_demo_account(142)
            
        with allure.step("Assert: Exception is caught and logged"):
            mock_logger.assert_called_once()
            assert "Failed to reset demo account: DB Error" in mock_logger.call_args[0][0]
