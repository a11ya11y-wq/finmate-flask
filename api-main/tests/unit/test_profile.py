import pytest
from core_service.profile.service import ProfileService
from unittest.mock import MagicMock
from core_service.exceptions import AuthenticationError, ResourceNotFound, BusinessLogicError
from pydantic import ValidationError
from decimal import Decimal



@pytest.fixture
def profile_uow(patch_uow):
    return patch_uow("core_service.profile.service.UnitOfWork")



VALID_USER_DATA = {
    "id": 1,
    "username": "testuser",
    "email": "test@gmail.com",
    "avatar": "avatars/default/default.svg",
    "currency": "USD",
}

class TestProfileGet:

    def test_get_user_data_success(self, profile_uow):

        user_data = VALID_USER_DATA
        fake_user = MagicMock()
        fake_user.to_dict.return_value = user_data

        profile_uow.profile.get_user_info.return_value = fake_user

        service = ProfileService()

        user_dict = service.get_user_data(1)

        profile_uow.profile.get_user_info.assert_called_once_with(1)

        assert user_dict == user_data

    def test_get_user_data_not_found(self, profile_uow):

        profile_uow.profile.get_user_info.return_value = None

        service = ProfileService()

        with pytest.raises(ResourceNotFound, match="User not found."):
            service.get_user_data(999)

        profile_uow.profile.get_user_info.assert_called_once_with(999)


class TestProfileUpdate:
    
    @pytest.mark.parametrize("update_data", [
        {"username": "ne32wuser"},
        {"currency": "EUR"},
        {"avatar": "avatars/default/9.svg"},
        {"username": "new1user", "currency": "EUR"},
        {"username": "new41user", "avatar": "avatars/default/2.svg"},
        {"currency": "EUR", "avatar": "avatars/default/1.svg"},
    ])
    def test_update_user_success(self, profile_uow, update_data):
        """Test successful user update"""
        user_obj = MagicMock(**VALID_USER_DATA)
        profile_uow.profile.get_user_info.return_value = user_obj
        profile_uow.profile.get_by_username.return_value = None

        service = ProfileService()

        service.update_user(1, update_data)

        args, _ = profile_uow.profile.update_user.call_args
        update_payload = args[1]

        for field in update_data:
            assert update_payload[field] == update_data[field]

        profile_uow.profile.get_user_info.assert_called_once_with(1)
        profile_uow.profile.update_user.assert_called_once_with(user_obj, update_data)
        profile_uow.commit.assert_called_once()

    @pytest.mark.parametrize("update_data", [
        {"username": "1"},  # Username too short
        {"username": "a"*33},  # Username too long
        {"currency": "GBP"},  # Invalid currency
        {"avatar": "a"*201},  # Avatar URL too long
        {"avatar": "a"*4},  # Avatar URL too short
        {"username": "   "},  # Invalid username
        {"avatar": "   "},
        {"username": "validuser", "avatar": "2"},  # Invalid avatar with valid username
        {"username": "a"*33, "currency": "GBP", "avatar": "a"*201},  # All fields invalid
    ])
    def test_update_user_no_valid_fields(self, profile_uow, update_data):
        """Test validation schema with no valid fields"""
        user_obj = MagicMock(**VALID_USER_DATA)
        profile_uow.profile.get_user_info.return_value = user_obj

        service = ProfileService()

        with pytest.raises(ValidationError):
            service.update_user(1, update_data)

        profile_uow.profile.get_user_info.assert_not_called()
        profile_uow.profile.update_user.assert_not_called()
        profile_uow.commit.assert_not_called()

    @pytest.mark.parametrize("update_data", [
        {},  # No fields
        {"username": None, "currency": None, "avatar": None},  # All fields None
        {"username": None},  # Username None
        {"currency": None},  # Currency None
        {"avatar": None},  # Avatar None
        {"username": None, "currency": None},  # Username and Currency None
        {"username": None, "avatar": None},  # Username and Avatar None
        {"currency": None, "avatar": None},  # Currency and Avatar None
    ])
    def test_update_user_emty_fields(self, profile_uow, update_data):
        """Test validation schema with empty fields"""
        user_obj = MagicMock(**VALID_USER_DATA)
        profile_uow.profile.get_user_info.return_value = user_obj

        service = ProfileService()

        with pytest.raises(BusinessLogicError, match="No valid fields to update."):
            service.update_user(1, update_data)

        profile_uow.profile.get_user_info.assert_not_called()
        profile_uow.profile.update_user.assert_not_called()
        profile_uow.commit.assert_not_called()

    def test_update_user_not_found(self, profile_uow):
        """Test updating a non-existent user"""
        profile_uow.profile.get_user_info.return_value = None

        service = ProfileService()

        with pytest.raises(ResourceNotFound, match="User not found."):
            service.update_user(999, {"username": "newuser"})

        profile_uow.profile.get_user_info.assert_called_once_with(999)
        profile_uow.profile.update_user.assert_not_called()
        profile_uow.commit.assert_not_called()

    def test_update_user_username_taken(self, profile_uow):
        """Test updating username to one that is already taken"""
        user_obj = MagicMock(**VALID_USER_DATA)
        profile_uow.profile.get_user_info.return_value = user_obj

        existing_user = MagicMock(id=2, username="existinguser")
        profile_uow.profile.get_by_username.return_value = existing_user

        service = ProfileService()

        with pytest.raises(BusinessLogicError, match="Username already taken."):
            service.update_user(1, {"username": "existinguser"})

        profile_uow.profile.get_user_info.assert_called_once_with(1)
        profile_uow.profile.get_by_username.assert_called_once_with("existinguser")
        profile_uow.profile.update_user.assert_not_called()
        profile_uow.commit.assert_not_called()

    def test_update_user_invalid_avatar(self, profile_uow):
        """Test updating avatar to an invalid selection"""
        user_obj = MagicMock(**VALID_USER_DATA)
        profile_uow.profile.get_user_info.return_value = user_obj

        service = ProfileService()

        with pytest.raises(BusinessLogicError, match="Invalid avatar selection."):
            service.update_user(1, {"avatar": "avatars/default/invalid.svg"})

        profile_uow.profile.get_user_info.assert_called_once_with(1)
        profile_uow.profile.update_user.assert_not_called()
        profile_uow.commit.assert_not_called()


class TestDeleteUser:

    def test_delete_user_success(self, profile_uow):
        """Test successful user deletion"""
        user_obj = MagicMock(**VALID_USER_DATA)
        profile_uow.profile.get_user_info.return_value = user_obj

        service = ProfileService()

        result = service.delete_user(1)

        profile_uow.profile.get_user_info.assert_called_once_with(1)
        profile_uow.profile.delete_user.assert_called_once_with(user_obj)
        profile_uow.commit.assert_called_once()

        assert result is True

    def test_delete_user_not_found(self, profile_uow):
        """Test deleting a non-existent user"""
        profile_uow.profile.get_user_info.return_value = None

        service = ProfileService()

        with pytest.raises(ResourceNotFound, match="User not found."):
            service.delete_user(999)

        profile_uow.profile.get_user_info.assert_called_once_with(999)
        profile_uow.profile.delete_user.assert_not_called()
        profile_uow.commit.assert_not_called()


VALID_PASSWORD_CHANGE_DATA = {
            "old_password": "oldpassword",
            "new_password": "newsecurepassword",
            "confirm_password": "newsecurepassword"
        }

class TestChangePassword:

    def test_change_password_success(self, profile_uow, mocker):
        """Test successful password change"""

        user_obj = MagicMock(**VALID_USER_DATA)
        user_obj.password = "oldpassword"

        user_obj.chek_hash_pwd.return_value = True

        profile_uow.profile.get_user_info.return_value = user_obj

        mock_hash = mocker.patch("core_service.profile.service.generate_password_hash", return_value="new_hashed_password")

        service = ProfileService()
        result = service.change_password(1, VALID_PASSWORD_CHANGE_DATA)

        assert result is True

        mock_hash.assert_called_once_with("newsecurepassword")

        profile_uow.profile.change_password_hash.assert_called_once_with(user_obj, "new_hashed_password")
        profile_uow.commit.assert_called_once()

    def test_change_password_invalid_old_password(self, profile_uow):
        """Test password change with invalid old password"""

        user_obj = MagicMock(**VALID_USER_DATA)
        user_obj.password = "oldpassword"

        user_obj.chek_hash_pwd.return_value = False

        profile_uow.profile.get_user_info.return_value = user_obj

        service = ProfileService()

        with pytest.raises(AuthenticationError, match="Invalid old password."):
            service.change_password(1, VALID_PASSWORD_CHANGE_DATA)

        profile_uow.profile.get_user_info.assert_called_once_with(1)
        profile_uow.profile.change_password_hash.assert_not_called()
        profile_uow.commit.assert_not_called()


    @pytest.mark.parametrize("update_data", [
        {"old_password": "oldpassword", "new_password": "short", "confirm_password": "short"},  # New password too short
        {"old_password": "oldpassword", "new_password": "a"*33, "confirm_password": "a"*33},  # New password too long
        {"old_password": "oldpassword", "new_password": "newpassword", "confirm_password": "different"},  # Confirmation does not match
        {"old_password": "oldpassword", "new_password": "oldpassword", "confirm_password": "oldpassword"},  # New password same as old
        {"old_password": "oldpassword", "new_password": "   ", "confirm_password": "   "},  # New password invalid
        {"old_password": "oldpassword", "new_password": "validnewpassword", "confirm_password": "   "},  # Confirmation invalid with valid new password
    ])
    def test_change_password_validation_error(self, profile_uow, update_data):
        """Test password change with invalid input data"""

        user_obj = MagicMock(**VALID_USER_DATA)
        user_obj.password = "oldpassword"

        user_obj.chek_hash_pwd.return_value = True

        profile_uow.profile.get_user_info.return_value = user_obj

        service = ProfileService()

        with pytest.raises(ValidationError):
            service.change_password(1, update_data)

        profile_uow.profile.get_user_info.assert_not_called()
        profile_uow.profile.change_password_hash.assert_not_called()
        profile_uow.commit.assert_not_called()

    def test_change_password_user_not_found(self, profile_uow):
        """Test password change for a non-existent user"""
        profile_uow.profile.get_user_info.return_value = None

        service = ProfileService()

        with pytest.raises(ResourceNotFound, match="User not found."):
            service.change_password(999, VALID_PASSWORD_CHANGE_DATA)

        profile_uow.profile.get_user_info.assert_called_once_with(999)
        profile_uow.profile.change_password_hash.assert_not_called()
        profile_uow.commit.assert_not_called()


class TestUpdateMonoToken:

    def test_update_mono_token_success(self, profile_uow, mocker):
        """Test successful MonoToken update"""

        user_obj = MagicMock(**VALID_USER_DATA)

        mock_app = MagicMock()
        mock_app.config = {"ENCRYPTION_KEY": "fake_key_for_testing"}
        mocker.patch("core_service.profile.service.current_app", mock_app)

        mock_fernet_class = mocker.patch("core_service.profile.service.Fernet")
    
        mock_instance = mock_fernet_class.return_value
        mock_instance.encrypt.return_value = b"fake_encrypted_token"
        profile_uow.profile.get_user_info.return_value = user_obj

        service = ProfileService()
        result = service.update_mono_token(1, {"token": "a"*44})

        profile_uow.profile.get_user_info.assert_called_once_with(1)
        profile_uow.profile.update_user.assert_called_once_with(user_obj, {'monobank_api_token': b'fake_encrypted_token'})
        profile_uow.commit.assert_called_once()

    @pytest.mark.parametrize("update_data", [
        {"token": "shorttoken"},  # Token too short
        {"token": "a"*45},  # Token too long
        {"token": "   "},  # Token invalid
        {"token": None},  # Token None
    ])
    def test_update_mono_token_failed(self, profile_uow, update_data):
        """Test MonoToken update with invalid token"""

        user_obj = MagicMock(**VALID_USER_DATA)

        profile_uow.profile.get_user_info.return_value = user_obj

        service = ProfileService()

        with pytest.raises(ValidationError):
            service.update_mono_token(1, update_data)

        profile_uow.profile.get_user_info.assert_not_called()
        profile_uow.profile.update_user.assert_not_called()
        profile_uow.commit.assert_not_called()

    def test_update_mono_token_user_not_found(self, profile_uow, mocker):
        """Test MonoToken update for a non-existent user"""
        profile_uow.profile.get_user_info.return_value = None
        mock_app = MagicMock()
        mock_app.config = {"ENCRYPTION_KEY": "fake_key_for_testing"}
        mocker.patch("core_service.profile.service.current_app", mock_app)

        mock_fernet_class = mocker.patch("core_service.profile.service.Fernet")
    
        mock_instance = mock_fernet_class.return_value
        mock_instance.encrypt.return_value = b"fake_encrypted_token"

        service = ProfileService()

        with pytest.raises(ResourceNotFound, match="User not found."):
            service.update_mono_token(999, {"token": "a"*44})

        profile_uow.profile.get_user_info.assert_called_once_with(999)
        profile_uow.profile.update_user.assert_not_called()
        profile_uow.commit.assert_not_called()


class TestDeleteMonoToken:
    def test_delete_mono_token_success(self, profile_uow):
        """Test successful MonoToken deletion"""

        user_obj = MagicMock(**VALID_USER_DATA)

        profile_uow.profile.get_user_info.return_value = user_obj

        service = ProfileService()
        result = service.delete_mono_token(1)

        profile_uow.profile.get_user_info.assert_called_once_with(1)
        profile_uow.profile.delete_monobank_token.assert_called_once_with(user_obj)
        profile_uow.commit.assert_called_once()

        assert result is True

    def test_delete_mono_token_user_not_found(self, profile_uow):
        """Test MonoToken deletion for a non-existent user"""
        profile_uow.profile.get_user_info.return_value = None

        service = ProfileService()

        with pytest.raises(ResourceNotFound, match="User not found."):
            service.delete_mono_token(999)

        profile_uow.profile.get_user_info.assert_called_once_with(999)
        profile_uow.profile.delete_monobank_token.assert_not_called()
        profile_uow.commit.assert_not_called()


class TestRecalculateInitialPoint:

    def test_recalculate_initial_point_success(self, profile_uow):
        """Verify that the method correctly recalculates the initial point based on last_real_balance and current Mono balance"""
        user_id = 1
        user_obj = MagicMock(last_real_balance=1000)

        profile_uow.profile.get_user_info.return_value = user_obj
        profile_uow.transactions.get_current_balance_mono.return_value = Decimal("300")
        
        service = ProfileService()
        result = service.recalculate_initial_point(profile_uow, user_id)

        assert result == Decimal("700")

        profile_uow.profile.setup_initial_balance.assert_called_once_with(user_obj, Decimal("700"))
        profile_uow.profile.get_user_info.assert_called_once_with(user_id)
        profile_uow.transactions.get_current_balance_mono.assert_called_once_with(user_id)

    def test_recalculate_initial_point_with_none_values(self, profile_uow):
        """Verify the method handles None values correctly"""
        user_id = 1
        user_obj = MagicMock(last_real_balance=None)
        profile_uow.profile.get_user_info.return_value = user_obj
        profile_uow.transactions.get_current_balance_mono.return_value = None
        
        service = ProfileService()
        
        result = service.recalculate_initial_point(profile_uow, user_id)
        
        assert result == Decimal("0")
        profile_uow.profile.setup_initial_balance.assert_called_once_with(user_obj, Decimal("0"))

    def test_recalculate_initial_point_user_not_found(self, profile_uow):
        """Verify that the method raises an error when the user is not found"""
        profile_uow.profile.get_user_info.return_value = None
        
        service = ProfileService()
        
        with pytest.raises(ResourceNotFound, match="User not found."):
            service.recalculate_initial_point(profile_uow, 999)
            
        profile_uow.profile.setup_initial_balance.assert_not_called()
