from decimal import Decimal
from unittest.mock import MagicMock

import allure
import pytest
from core_service.exceptions import (
    AuthenticationError,
    BusinessLogicError,
    ResourceNotFound,
)
from core_service.profile.service import ProfileService
from pydantic import ValidationError


@pytest.fixture
@allure.title("Initialize Mocked Profile UOW")
def profile_uow():
    with allure.step("Initialize MagicMock for Profile Unit of Work"):
        return MagicMock()


VALID_USER_DATA = {
    "id": 1,
    "username": "testuser",
    "email": "test@gmail.com",
    "avatar": "avatars/default/default.svg",
    "currency": "USD",
}


@allure.feature("Profile Management")
@allure.story("Retrieve Profile")
class TestProfileGet:

    @allure.title("Successfully retrieve user profile data")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_get_user_data_success(self, profile_uow):
        with allure.step("Arrange: Mock user data"):
            user_data = VALID_USER_DATA
            fake_user = MagicMock()
            fake_user.to_dict.return_value = user_data
            profile_uow.profile.get_user_info.return_value = fake_user
            service = ProfileService(profile_uow)

        with allure.step("Act: Fetch user data"):
            user_dict = service.get_user_data(1)

        with allure.step("Assert: Verify response matches mocked data"):
            profile_uow.profile.get_user_info.assert_called_once_with(1)
            assert user_dict == user_data

    @allure.title("Fail to retrieve non-existent profile")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_user_data_not_found(self, profile_uow):
        with allure.step("Arrange: Mock user not found (None)"):
            profile_uow.profile.get_user_info.return_value = None
            service = ProfileService(profile_uow)

        with allure.step("Act & Assert: Expect ResourceNotFound"):
            with pytest.raises(ResourceNotFound, match="User not found."):
                service.get_user_data(999)

        with allure.step("Assert: Verify UOW was called"):
            profile_uow.profile.get_user_info.assert_called_once_with(999)


@allure.feature("Profile Management")
@allure.story("Update Profile")
class TestProfileUpdate:

    @allure.title("Successfully update valid user fields")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize(
        "update_data",
        [
            {"username": "ne32wuser"},
            {"currency": "EUR"},
            {"avatar": "avatars/default/9.svg"},
            {"username": "new1user", "currency": "EUR"},
            {"username": "new41user", "avatar": "avatars/default/2.svg"},
            {"currency": "EUR", "avatar": "avatars/default/1.svg"},
        ],
    )
    def test_update_user_success(self, profile_uow, update_data):
        """Test successful user update"""
        with allure.step("Arrange: Mock existing user and ensure new username is free"):
            user_obj = MagicMock(**VALID_USER_DATA)
            profile_uow.profile.get_user_info.return_value = user_obj
            profile_uow.profile.get_by_username.return_value = None
            service = ProfileService(profile_uow)

        with allure.step("Act: Call update_user"):
            service.update_user(1, update_data)

        with allure.step("Assert: Verify payload matches submitted data"):
            args, _ = profile_uow.profile.update_user.call_args
            update_payload = args[1]
            for field in update_data:
                assert update_payload[field] == update_data[field]
            profile_uow.profile.get_user_info.assert_called_once_with(1)
            profile_uow.profile.update_user.assert_called_once_with(
                user_obj, update_data
            )

    @allure.title("Validation errors on invalid profile fields")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize(
        "update_data",
        [
            {"username": "1"},  # Username too short
            {"username": "a" * 33},  # Username too long
            {"currency": "GBP"},  # Invalid currency
            {"avatar": "a" * 201},  # Avatar URL too long
            {"avatar": "a" * 4},  # Avatar URL too short
            {"username": "   "},  # Invalid username
            {"avatar": "   "},
            {
                "username": "validuser",
                "avatar": "2",
            },  # Invalid avatar with valid username
            {
                "username": "a" * 33,
                "currency": "GBP",
                "avatar": "a" * 201,
            },  # All fields invalid
        ],
    )
    def test_update_user_no_valid_fields(self, profile_uow, update_data):
        """Test validation schema with no valid fields"""
        with allure.step("Arrange: Mock existing user"):
            user_obj = MagicMock(**VALID_USER_DATA)
            profile_uow.profile.get_user_info.return_value = user_obj
            service = ProfileService(profile_uow)

        with allure.step("Act & Assert: Expect ValidationError"):
            with pytest.raises(ValidationError):
                service.update_user(1, update_data)

        with allure.step("Assert: Ensure DB was not queried or updated"):
            profile_uow.profile.get_user_info.assert_not_called()
            profile_uow.profile.update_user.assert_not_called()

    @allure.title("Fail to update if payload contains empty/None fields")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize(
        "update_data",
        [
            {},  # No fields
            {"username": None, "currency": None, "avatar": None},  # All fields None
            {"username": None},  # Username None
            {"currency": None},  # Currency None
            {"avatar": None},  # Avatar None
            {"username": None, "currency": None},  # Username and Currency None
            {"username": None, "avatar": None},  # Username and Avatar None
            {"currency": None, "avatar": None},  # Currency and Avatar None
        ],
    )
    def test_update_user_emty_fields(self, profile_uow, update_data):
        """Test validation schema with empty fields"""
        with allure.step("Arrange: Mock existing user"):
            user_obj = MagicMock(**VALID_USER_DATA)
            profile_uow.profile.get_user_info.return_value = user_obj
            service = ProfileService(profile_uow)

        with allure.step("Act & Assert: Expect BusinessLogicError"):
            with pytest.raises(BusinessLogicError, match="No valid fields to update."):
                service.update_user(1, update_data)

        with allure.step("Assert: Ensure DB was not queried or updated"):
            profile_uow.profile.get_user_info.assert_not_called()
            profile_uow.profile.update_user.assert_not_called()

    @allure.title("Fail to update non-existent user")
    @allure.severity(allure.severity_level.NORMAL)
    def test_update_user_not_found(self, profile_uow):
        """Test updating a non-existent user"""
        with allure.step("Arrange: Mock user not found"):
            profile_uow.profile.get_user_info.return_value = None
            service = ProfileService(profile_uow)

        with allure.step("Act & Assert: Expect ResourceNotFound"):
            with pytest.raises(ResourceNotFound, match="User not found."):
                service.update_user(999, {"username": "newuser"})

        with allure.step("Assert: Ensure update was not called"):
            profile_uow.profile.get_user_info.assert_called_once_with(999)
            profile_uow.profile.update_user.assert_not_called()

    @allure.title("Fail to update if username is already taken")
    @allure.severity(allure.severity_level.NORMAL)
    def test_update_user_username_taken(self, profile_uow):
        """Test updating username to one that is already taken"""
        with allure.step("Arrange: Mock existing duplicate username"):
            user_obj = MagicMock(**VALID_USER_DATA)
            profile_uow.profile.get_user_info.return_value = user_obj
            existing_user = MagicMock(id=2, username="existinguser")
            profile_uow.profile.get_by_username.return_value = existing_user
            service = ProfileService(profile_uow)

        with allure.step("Act & Assert: Expect BusinessLogicError"):
            with pytest.raises(BusinessLogicError, match="Username already taken."):
                service.update_user(1, {"username": "existinguser"})

        with allure.step("Assert: Ensure update was not called"):
            profile_uow.profile.get_user_info.assert_called_once_with(1)
            profile_uow.profile.get_by_username.assert_called_once_with("existinguser")
            profile_uow.profile.update_user.assert_not_called()

    @allure.title("Fail to update avatar with invalid selection")
    @allure.severity(allure.severity_level.NORMAL)
    def test_update_user_invalid_avatar(self, profile_uow):
        """Test updating avatar to an invalid selection"""
        with allure.step("Arrange: Mock existing user"):
            user_obj = MagicMock(**VALID_USER_DATA)
            profile_uow.profile.get_user_info.return_value = user_obj
            service = ProfileService(profile_uow)

        with allure.step("Act & Assert: Expect BusinessLogicError"):
            with pytest.raises(BusinessLogicError, match="Invalid avatar selection."):
                service.update_user(1, {"avatar": "avatars/default/invalid.svg"})

        with allure.step("Assert: Ensure update was not called"):
            profile_uow.profile.get_user_info.assert_called_once_with(1)
            profile_uow.profile.update_user.assert_not_called()


@allure.feature("Profile Management")
@allure.story("Delete Profile")
class TestDeleteUser:

    @allure.title("Successfully delete a user profile")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_user_success(self, profile_uow):
        """Test successful user deletion"""
        with allure.step("Arrange: Mock existing user"):
            user_obj = MagicMock(**VALID_USER_DATA)
            profile_uow.profile.get_user_info.return_value = user_obj
            service = ProfileService(profile_uow)

        with allure.step("Act: Call delete_user"):
            result = service.delete_user(1)

        with allure.step("Assert: Verify deletion method was called"):
            profile_uow.profile.get_user_info.assert_called_once_with(1)
            profile_uow.profile.delete_user.assert_called_once_with(user_obj)
            assert result is True

    @allure.title("Fail to delete non-existent user profile")
    @allure.severity(allure.severity_level.NORMAL)
    def test_delete_user_not_found(self, profile_uow):
        """Test deleting a non-existent user"""
        with allure.step("Arrange: Mock user not found"):
            profile_uow.profile.get_user_info.return_value = None
            service = ProfileService(profile_uow)

        with allure.step("Act & Assert: Expect ResourceNotFound"):
            with pytest.raises(ResourceNotFound, match="User not found."):
                service.delete_user(999)

        with allure.step("Assert: Verify delete was not called"):
            profile_uow.profile.get_user_info.assert_called_once_with(999)
            profile_uow.profile.delete_user.assert_not_called()


VALID_PASSWORD_CHANGE_DATA = {
    "old_password": "oldpassword",
    "new_password": "newsecurepassword",
    "confirm_password": "newsecurepassword",
}


@allure.feature("Profile Management")
@allure.story("Change Password")
class TestChangePassword:

    @allure.title("Successfully change user password")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_change_password_success(self, profile_uow, mocker):
        """Test successful password change"""
        with allure.step("Arrange: Mock password verification and hashing"):
            user_obj = MagicMock(**VALID_USER_DATA)
            user_obj.password = "oldpassword"
            user_obj.chek_hash_pwd.return_value = True
            profile_uow.profile.get_user_info.return_value = user_obj

            mock_hash = mocker.patch(
                "core_service.profile.service.generate_password_hash",
                return_value="new_hashed_password",
            )
            service = ProfileService(profile_uow)

        with allure.step("Act: Call change_password"):
            result = service.change_password(1, VALID_PASSWORD_CHANGE_DATA)

        with allure.step("Assert: Verify hash generation and DB update"):
            assert result is True
            mock_hash.assert_called_once_with("newsecurepassword")
            profile_uow.profile.change_password_hash.assert_called_once_with(
                user_obj, "new_hashed_password"
            )

    @allure.title("Fail to change password with incorrect old password")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_change_password_invalid_old_password(self, profile_uow):
        """Test password change with invalid old password"""
        with allure.step("Arrange: Mock hash check failure"):
            user_obj = MagicMock(**VALID_USER_DATA)
            user_obj.password = "oldpassword"
            user_obj.chek_hash_pwd.return_value = False
            profile_uow.profile.get_user_info.return_value = user_obj
            service = ProfileService(profile_uow)

        with allure.step("Act & Assert: Expect AuthenticationError"):
            with pytest.raises(AuthenticationError, match="Invalid old password."):
                service.change_password(1, VALID_PASSWORD_CHANGE_DATA)

        with allure.step("Assert: Verify DB was not updated"):
            profile_uow.profile.get_user_info.assert_called_once_with(1)
            profile_uow.profile.change_password_hash.assert_not_called()

    @allure.title("Validation errors on invalid password payloads")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize(
        "update_data",
        [
            {
                "old_password": "oldpassword",
                "new_password": "short",
                "confirm_password": "short",
            },  # New password too short
            {
                "old_password": "oldpassword",
                "new_password": "a" * 33,
                "confirm_password": "a" * 33,
            },  # New password too long
            {
                "old_password": "oldpassword",
                "new_password": "newpassword",
                "confirm_password": "different",
            },  # Confirmation does not match
            {
                "old_password": "oldpassword",
                "new_password": "oldpassword",
                "confirm_password": "oldpassword",
            },  # New password same as old
            {
                "old_password": "oldpassword",
                "new_password": "   ",
                "confirm_password": "   ",
            },  # New password invalid
            {
                "old_password": "oldpassword",
                "new_password": "validnewpassword",
                "confirm_password": "   ",
            },  # Confirmation invalid with valid new password
        ],
    )
    def test_change_password_validation_error(self, profile_uow, update_data):
        """Test password change with invalid input data"""
        with allure.step("Arrange: Mock existing user"):
            user_obj = MagicMock(**VALID_USER_DATA)
            user_obj.password = "oldpassword"
            user_obj.chek_hash_pwd.return_value = True
            profile_uow.profile.get_user_info.return_value = user_obj
            service = ProfileService(profile_uow)

        with allure.step("Act & Assert: Expect ValidationError"):
            with pytest.raises(ValidationError):
                service.change_password(1, update_data)

        with allure.step("Assert: Ensure update was not called"):
            profile_uow.profile.get_user_info.assert_not_called()
            profile_uow.profile.change_password_hash.assert_not_called()

    @allure.title("Fail to change password for non-existent user")
    @allure.severity(allure.severity_level.NORMAL)
    def test_change_password_user_not_found(self, profile_uow):
        """Test password change for a non-existent user"""
        with allure.step("Arrange: Mock user not found"):
            profile_uow.profile.get_user_info.return_value = None
            service = ProfileService(profile_uow)

        with allure.step("Act & Assert: Expect ResourceNotFound"):
            with pytest.raises(ResourceNotFound, match="User not found."):
                service.change_password(999, VALID_PASSWORD_CHANGE_DATA)

        with allure.step("Assert: Ensure DB was not updated"):
            profile_uow.profile.get_user_info.assert_called_once_with(999)
            profile_uow.profile.change_password_hash.assert_not_called()


@allure.feature("Profile Management")
@allure.story("Update Mono Token")
class TestUpdateMonoToken:

    @allure.title("Successfully update Monobank API token (encryption check)")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_update_mono_token_success(self, profile_uow, mocker):
        """Test successful MonoToken update"""
        with allure.step("Arrange: Mock Flask config and Fernet encryption"):
            user_obj = MagicMock(**VALID_USER_DATA)
            mock_app = MagicMock()
            mock_app.config = {"ENCRYPTION_KEY": "fake_key_for_testing"}
            mocker.patch("core_service.profile.service.current_app", mock_app)

            mock_fernet_class = mocker.patch("core_service.profile.service.Fernet")
            mock_instance = mock_fernet_class.return_value
            mock_instance.encrypt.return_value = b"fake_encrypted_token"
            profile_uow.profile.get_user_info.return_value = user_obj
            service = ProfileService(profile_uow)

        with allure.step("Act: Call update_mono_token"):
            result = service.update_mono_token(1, {"token": "a" * 44})

        with allure.step("Assert: Verify encrypted token is saved"):
            profile_uow.profile.get_user_info.assert_called_once_with(1)
            profile_uow.profile.update_user.assert_called_once_with(
                user_obj, {"monobank_api_token": b"fake_encrypted_token"}
            )

    @allure.title("Validation errors on invalid Monobank API token")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize(
        "update_data",
        [
            {"token": "shorttoken"},  # Token too short
            {"token": "a" * 45},  # Token too long
            {"token": "   "},  # Token invalid
            {"token": None},  # Token None
        ],
    )
    def test_update_mono_token_failed(self, profile_uow, update_data):
        """Test MonoToken update with invalid token"""
        with allure.step("Arrange: Mock existing user"):
            user_obj = MagicMock(**VALID_USER_DATA)
            profile_uow.profile.get_user_info.return_value = user_obj
            service = ProfileService(profile_uow)

        with allure.step("Act & Assert: Expect ValidationError"):
            with pytest.raises(ValidationError):
                service.update_mono_token(1, update_data)

        with allure.step("Assert: Ensure update was not called"):
            profile_uow.profile.get_user_info.assert_not_called()
            profile_uow.profile.update_user.assert_not_called()

    @allure.title("Fail to update Monobank token for non-existent user")
    @allure.severity(allure.severity_level.NORMAL)
    def test_update_mono_token_user_not_found(self, profile_uow, mocker):
        """Test MonoToken update for a non-existent user"""
        with allure.step("Arrange: Mock user not found and encryption logic"):
            profile_uow.profile.get_user_info.return_value = None
            mock_app = MagicMock()
            mock_app.config = {"ENCRYPTION_KEY": "fake_key_for_testing"}
            mocker.patch("core_service.profile.service.current_app", mock_app)

            mock_fernet_class = mocker.patch("core_service.profile.service.Fernet")
            mock_instance = mock_fernet_class.return_value
            mock_instance.encrypt.return_value = b"fake_encrypted_token"
            service = ProfileService(profile_uow)

        with allure.step("Act & Assert: Expect ResourceNotFound"):
            with pytest.raises(ResourceNotFound, match="User not found."):
                service.update_mono_token(999, {"token": "a" * 44})

        with allure.step("Assert: Ensure update was not called"):
            profile_uow.profile.get_user_info.assert_called_once_with(999)
            profile_uow.profile.update_user.assert_not_called()


@allure.feature("Profile Management")
@allure.story("Delete Mono Token")
class TestDeleteMonoToken:

    @allure.title("Successfully delete Monobank API token")
    @allure.severity(allure.severity_level.NORMAL)
    def test_delete_mono_token_success(self, profile_uow):
        """Test successful MonoToken deletion"""
        with allure.step("Arrange: Mock existing user"):
            user_obj = MagicMock(**VALID_USER_DATA)
            profile_uow.profile.get_user_info.return_value = user_obj
            service = ProfileService(profile_uow)

        with allure.step("Act: Call delete_mono_token"):
            result = service.delete_mono_token(1)

        with allure.step("Assert: Verify token deletion method is called"):
            profile_uow.profile.get_user_info.assert_called_once_with(1)
            profile_uow.profile.delete_monobank_token.assert_called_once_with(user_obj)
            assert result is True

    @allure.title("Fail to delete Monobank token for non-existent user")
    @allure.severity(allure.severity_level.NORMAL)
    def test_delete_mono_token_user_not_found(self, profile_uow):
        """Test MonoToken deletion for a non-existent user"""
        with allure.step("Arrange: Mock user not found"):
            profile_uow.profile.get_user_info.return_value = None
            service = ProfileService(profile_uow)

        with allure.step("Act & Assert: Expect ResourceNotFound"):
            with pytest.raises(ResourceNotFound, match="User not found."):
                service.delete_mono_token(999)

        with allure.step("Assert: Ensure delete was not called"):
            profile_uow.profile.get_user_info.assert_called_once_with(999)
            profile_uow.profile.delete_monobank_token.assert_not_called()


@allure.feature("Profile Management")
@allure.story("Recalculate Initial Point")
class TestRecalculateInitialPoint:

    @allure.title("Successfully recalculate initial point balance")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_recalculate_initial_point_success(self, profile_uow):
        """Verify that the method correctly recalculates the initial point based on last_real_balance and current Mono balance"""
        with allure.step("Arrange: Mock user balance and current Mono balance"):
            user_id = 1
            user_obj = MagicMock(last_real_balance=1000)
            profile_uow.profile.get_user_info.return_value = user_obj
            profile_uow.transactions.get_current_balance_mono.return_value = Decimal(
                "300"
            )
            service = ProfileService(profile_uow)

        with allure.step("Act: Call recalculate_initial_point"):
            result = service.recalculate_initial_point(user_id)

        with allure.step("Assert: Verify math (1000 - 300) and DB setup call"):
            assert result == Decimal("700")
            profile_uow.profile.setup_initial_balance.assert_called_once_with(
                user_obj, Decimal("700")
            )
            profile_uow.profile.get_user_info.assert_called_once_with(user_id)
            profile_uow.transactions.get_current_balance_mono.assert_called_once_with(
                user_id
            )

    @allure.title("Handle None values gracefully during recalculation")
    @allure.severity(allure.severity_level.NORMAL)
    def test_recalculate_initial_point_with_none_values(self, profile_uow):
        """Verify the method handles None values correctly"""
        with allure.step("Arrange: Mock user with no balance data"):
            user_id = 1
            user_obj = MagicMock(last_real_balance=None)
            profile_uow.profile.get_user_info.return_value = user_obj
            profile_uow.transactions.get_current_balance_mono.return_value = None
            service = ProfileService(profile_uow)

        with allure.step("Act: Call recalculate_initial_point"):
            result = service.recalculate_initial_point(user_id)

        with allure.step("Assert: Verify fallback to zero"):
            assert result == Decimal("0")
            profile_uow.profile.setup_initial_balance.assert_called_once_with(
                user_obj, Decimal("0")
            )

    @allure.title("Fail recalculation for non-existent user")
    @allure.severity(allure.severity_level.NORMAL)
    def test_recalculate_initial_point_user_not_found(self, profile_uow):
        """Verify that the method raises an error when the user is not found"""
        with allure.step("Arrange: Mock user not found"):
            profile_uow.profile.get_user_info.return_value = None
            service = ProfileService(profile_uow)

        with allure.step("Act & Assert: Expect ResourceNotFound"):
            with pytest.raises(ResourceNotFound, match="User not found."):
                service.recalculate_initial_point(999)

        with allure.step("Assert: Ensure setup was not called"):
            profile_uow.profile.setup_initial_balance.assert_not_called()
