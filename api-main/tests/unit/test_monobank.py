from decimal import Decimal
import pytest
import requests
from unittest.mock import call

from core_service.exceptions import BusinessLogicError, ThrottlingError, ForbiddenError
from core_service.models import Users, Category
from core_service.monobank.service import MonobankService

FAKE_CLIENT_INFO = {"accounts": [{"id": "ACC_ID_001", 'type': 'black', 'balance': '10000000'}]}
FAKE_MONO_TRANSACTIONS = [
    {"id": "mono_id_NEW_1", "amount": 10000, "description": "Sushi", "time": 1700000000, "mcc": 5812},
    {"id": "mono_id_OLD_2", "amount": 5000, "description": "Rent", "time": 1700000000, "mcc": 4900},
]


@pytest.fixture
def mono_env(patch_uow, mocker):
    """
    Prepare a testing environment for MonobankService tests by mocking the Unit of Work, MonoAPI client, and ProfileService.
    """

    fake_uncat_category = Category(id=100, name="Uncategorized")
    fake_user = Users(id=1, monobank_api_token=b'FAKE_TOKEN')

    mock_uow = patch_uow("core_service.monobank.service.UnitOfWork")
    mock_uow.profile.get_user_info.return_value = fake_user
    mock_uow.categories.get_by_name_and_user.return_value = fake_uncat_category
    mock_uow.categories.get_all_categories.return_value = []

    mock_mono_client = mocker.patch("core_service.monobank.service.MonoAPI", autospec=True).return_value
    mock_mono_client.get_client_info.return_value = FAKE_CLIENT_INFO

    mock_profile_service = mocker.patch("core_service.monobank.service.ProfileService", autospec=True).return_value
    mock_profile_service.recalculate_initial_point.return_value = 1000

    return {
        "client": mock_mono_client,
        "uow": mock_uow,
        "profile_svc": mock_profile_service
    }


class TestMonobankService:

    def test_sync_tx_success(self, mono_env, app):
        mono_env["client"].get_transactions.return_value = FAKE_MONO_TRANSACTIONS
        mono_env["uow"].transactions.get_existing_mono_ids.return_value = {"mono_id_OLD_2"}
        mono_env["uow"].transactions.bulk_insert_transactions.return_value = 1

        service = MonobankService()

        with app.app_context():
            added_count = service.sync_tx(user_id=1)

        assert added_count == 1
        mono_env["uow"].transactions.bulk_insert_transactions.assert_called_once()

        transactions_saved = mono_env["uow"].transactions.bulk_insert_transactions.call_args[0][0]
        assert len(transactions_saved) == 1
        assert transactions_saved[0].amount == Decimal('100.00')
        assert transactions_saved[0].mono_id == "mono_id_NEW_1"

    def test_sync_tx_fails_on_rate_limit(self, mono_env, app):
        RATE_LIMIT_ERROR = {"errorDescription": "Too many requests", "status_code": 429}
        mono_env["client"].get_transactions.return_value = RATE_LIMIT_ERROR

        service = MonobankService()

        with pytest.raises(ThrottlingError) as excinfo:
            with app.app_context():
                service.sync_tx(user_id=1)

        assert "Too many requests" in str(excinfo.value)
        mono_env["uow"].transactions.bulk_insert_transactions.assert_not_called()
        mono_env["uow"].transactions.get_existing_mono_ids.assert_not_called()

    def test_sync_tx_no_new_tx(self, mono_env, app):
        mono_env["client"].get_transactions.return_value = []
        mono_env["uow"].transactions.bulk_insert_transactions.return_value = 0

        service = MonobankService()

        with app.app_context():
            added_count = service.sync_tx(user_id=1)

        assert added_count == 0
        mono_env["uow"].transactions.bulk_insert_transactions.assert_not_called()

    def test_sync_tx_api_error(self, mono_env, app):
        mono_env["client"].get_transactions.side_effect = requests.RequestException("Monobank is down")

        service = MonobankService()

        with pytest.raises(requests.RequestException):
            with app.app_context():
                service.sync_tx(user_id=1)

        mono_env["uow"].transactions.bulk_insert_transactions.assert_not_called()

    def test_sync_tx_token_error(self, mono_env, app):
        no_token_user = Users(id=1, monobank_api_token=None)
        mono_env["uow"].profile.get_user_info.return_value = no_token_user

        service = MonobankService()

        with pytest.raises(BusinessLogicError, match="API token not found or user access denied."):
            with app.app_context():
                service.sync_tx(user_id=1)

        mono_env["uow"].transactions.bulk_insert_transactions.assert_not_called()

    def test_sync_tx_creates_uncat_and_maps_income(self, mono_env, app):
        INCOME_TX = [{"id": "mono_income_1", "amount": 15000, "description": "Salary", "time": 1700000000, "mcc": 1234}]
        mono_env["client"].get_transactions.return_value = INCOME_TX

        mono_env["uow"].categories.get_by_name_and_user.return_value = None
        fake_new_cat = Category(id=999, name="Uncategorized")
        mono_env["uow"].categories.create_category.return_value = fake_new_cat
        mono_env["uow"].transactions.bulk_insert_transactions.return_value = 1
        
        service = MonobankService()
        with app.app_context():
            service.sync_tx(user_id=1)

        mono_env["uow"].categories.create_category.assert_called_once_with(1, {"name": "Uncategorized"})
        
        transactions_saved = mono_env["uow"].transactions.bulk_insert_transactions.call_args[0][0]
        assert transactions_saved[0].transaction_type == 'income' # Дохід!
        assert transactions_saved[0].amount == Decimal('150.00')

    def test_sync_tx_commits_and_clears_cache(self, mono_env, app, mocker):
        mono_env["client"].get_transactions.return_value = FAKE_MONO_TRANSACTIONS
        mono_env["uow"].transactions.bulk_insert_transactions.return_value = 2
        mock_invalidate = mocker.patch("core_service.monobank.service.invalidate_cache")
        
        service = MonobankService()
        with app.app_context():
            service.sync_tx(user_id=1)

        mono_env["uow"].commit.assert_called_once()
        mono_env["uow"].profile.update_real_balance.assert_called_once()
        mono_env["profile_svc"].recalculate_initial_point.assert_called_once()

        assert mock_invalidate.call_count == 3
        mock_invalidate.assert_has_calls([
            call("dashboard:1:*"),
            call("budgets:1"),
            call("profile:1")
        ], any_order=True)

    def test_get_card_stats_selects_black_uah_card(self, mono_env, app):
        MULTI_CARDS_INFO = {"accounts": [
            {"id": "USD_CARD", "type": "black", "currencyCode": 840, "balance": 5000},
            {"id": "WHITE_CARD", "type": "white", "currencyCode": 980, "balance": 1000},
            {"id": "BLACK_UAH", "type": "black", "currencyCode": 980, "balance": 99900} # <- Має вибрати цю
        ]}
        mono_env["client"].get_client_info.return_value = MULTI_CARDS_INFO
        mono_env["client"].get_transactions.return_value = []
        
        service = MonobankService()
        with app.app_context():
            service.sync_tx(user_id=1)

        mono_env["client"].get_transactions.assert_called_once()
        args = mono_env["client"].get_transactions.call_args[0]
        assert args[0] == "BLACK_UAH" # account_id

    def test_sync_tx_no_accounts_found(self, mono_env, app):
        mono_env["client"].get_client_info.return_value = {"accounts": []}
        
        service = MonobankService()
        with pytest.raises(BusinessLogicError, match="No accounts found in Monobank"):
            with app.app_context():
                service.sync_tx(user_id=1)

    def test_sync_tx_forbidden_error_from_api(self, mono_env, app):
        mono_env["client"].get_client_info.return_value = {"errorDescription": "Unknown 'X-Token'"}
        
        service = MonobankService()
        with pytest.raises(ForbiddenError, match="Unknown 'X-Token'"):
            with app.app_context():
                service.sync_tx(user_id=1)