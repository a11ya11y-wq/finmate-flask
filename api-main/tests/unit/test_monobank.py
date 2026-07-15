from decimal import Decimal
from unittest.mock import MagicMock, call

import allure
import pytest
import requests
from core_service.exceptions import BusinessLogicError, ForbiddenError, ThrottlingError
from core_service.models import Category, Users
from core_service.monobank.service import MonobankService

FAKE_CLIENT_INFO = {
    "accounts": [{"id": "ACC_ID_001", "type": "black", "balance": "10000000"}]
}
FAKE_MONO_TRANSACTIONS = [
    {
        "id": "mono_id_NEW_1",
        "amount": 10000,
        "description": "Sushi",
        "time": 1700000000,
        "mcc": 5812,
    },
    {
        "id": "mono_id_OLD_2",
        "amount": 5000,
        "description": "Rent",
        "time": 1700000000,
        "mcc": 4900,
    },
]


@pytest.fixture
@allure.title("Initialize Mocked Monobank Environment")
def mono_env(mocker):
    with allure.step("Setup mock User and UOW"):
        fake_uncat_category = Category(id=100, name="Uncategorized")
        fake_user = Users(id=1, monobank_api_token=b"FAKE_TOKEN")

        mock_uow = MagicMock()
        mock_uow.profile.get_user_info.return_value = fake_user
        mock_uow.categories.get_by_name_and_user.return_value = fake_uncat_category
        mock_uow.categories.get_all_categories.return_value = []

    with allure.step("Patch MonoAPI client and ProfileService"):
        mock_mono_client = mocker.patch(
            "core_service.monobank.service.MonoAPI", autospec=True
        ).return_value
        mock_mono_client.get_client_info.return_value = FAKE_CLIENT_INFO

        mock_profile_service = mocker.patch(
            "core_service.monobank.service.ProfileService", autospec=True
        ).return_value
        mock_profile_service.recalculate_initial_point.return_value = 1000

    return {
        "client": mock_mono_client,
        "uow": mock_uow,
        "profile_svc": mock_profile_service,
    }


@allure.feature("Monobank Integration")
@allure.story("Transaction Synchronization")
class TestMonobankService:

    @allure.title("Successfully synchronize new transactions")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_sync_tx_success(self, mono_env, app):
        with allure.step("Arrange: Mock API response with new and old transactions"):
            mono_env["client"].get_transactions.return_value = FAKE_MONO_TRANSACTIONS
            mono_env["uow"].transactions.get_existing_mono_ids.return_value = {
                "mono_id_OLD_2"
            }
            mono_env["uow"].transactions.bulk_insert_transactions.return_value = 1
            service = MonobankService(mono_env["uow"])

        with allure.step("Act: Call sync_tx"):
            with app.app_context():
                added_count = service.sync_tx(user_id=1)

        with allure.step("Assert: Verify bulk insert and mapped amounts"):
            assert added_count == 1
            mono_env["uow"].transactions.bulk_insert_transactions.assert_called_once()
            transactions_saved = mono_env[
                "uow"
            ].transactions.bulk_insert_transactions.call_args[0][0]
            assert len(transactions_saved) == 1
            assert transactions_saved[0].amount == Decimal("100.00")
            assert transactions_saved[0].mono_id == "mono_id_NEW_1"

    @allure.title("Synchronization fails on Monobank rate limit (429)")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_sync_tx_fails_on_rate_limit(self, mono_env, app):
        with allure.step("Arrange: Mock rate limit error from MonoAPI"):
            RATE_LIMIT_ERROR = {
                "errorDescription": "Too many requests",
                "status_code": 429,
            }
            mono_env["client"].get_transactions.return_value = RATE_LIMIT_ERROR
            service = MonobankService(mono_env["uow"])

        with allure.step("Act & Assert: Expect ThrottlingError"):
            with pytest.raises(ThrottlingError) as excinfo:
                with app.app_context():
                    service.sync_tx(user_id=1)
            assert "Too many requests" in str(excinfo.value)

        with allure.step("Assert: Ensure DB was not modified"):
            mono_env["uow"].transactions.bulk_insert_transactions.assert_not_called()
            mono_env["uow"].transactions.get_existing_mono_ids.assert_not_called()

    @allure.title("Synchronization handles empty transaction list gracefully")
    @allure.severity(allure.severity_level.NORMAL)
    def test_sync_tx_no_new_tx(self, mono_env, app):
        with allure.step("Arrange: Mock empty transaction list"):
            mono_env["client"].get_transactions.return_value = []
            mono_env["uow"].transactions.bulk_insert_transactions.return_value = 0
            service = MonobankService(mono_env["uow"])

        with allure.step("Act: Call sync_tx"):
            with app.app_context():
                added_count = service.sync_tx(user_id=1)

        with allure.step("Assert: Ensure no insertions occurred"):
            assert added_count == 0
            mono_env["uow"].transactions.bulk_insert_transactions.assert_not_called()

    @allure.title("Synchronization fails on Monobank API exception")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_sync_tx_api_error(self, mono_env, app):
        with allure.step("Arrange: Mock RequestException from API"):
            mono_env["client"].get_transactions.side_effect = requests.RequestException(
                "Monobank is down"
            )
            service = MonobankService(mono_env["uow"])

        with allure.step("Act & Assert: Expect RequestException"):
            with pytest.raises(requests.RequestException):
                with app.app_context():
                    service.sync_tx(user_id=1)

        with allure.step("Assert: Ensure DB was not modified"):
            mono_env["uow"].transactions.bulk_insert_transactions.assert_not_called()

    @allure.title("Sync fails if user has no valid Mono API token")
    @allure.severity(allure.severity_level.NORMAL)
    def test_sync_tx_token_error(self, mono_env, app):
        with allure.step("Arrange: Mock user without token"):
            no_token_user = Users(id=1, monobank_api_token=None)
            mono_env["uow"].profile.get_user_info.return_value = no_token_user
            service = MonobankService(mono_env["uow"])

        with allure.step("Act & Assert: Expect BusinessLogicError"):
            with pytest.raises(
                BusinessLogicError, match="API token not found or user access denied."
            ):
                with app.app_context():
                    service.sync_tx(user_id=1)

        with allure.step("Assert: Ensure DB was not modified"):
            mono_env["uow"].transactions.bulk_insert_transactions.assert_not_called()

    @allure.title("Sync fails if user is not found in database")
    @allure.severity(allure.severity_level.NORMAL)
    def test_sync_tx_missing_user(self, mono_env, app):
        with allure.step("Arrange: Mock missing user"):
            mono_env["uow"].profile.get_user_info.return_value = None
            service = MonobankService(mono_env["uow"])

        with allure.step("Act & Assert: Expect BusinessLogicError"):
            with pytest.raises(
                BusinessLogicError, match="API token not found or user access denied."
            ):
                with app.app_context():
                    service.sync_tx(user_id=1)

        with allure.step("Assert: Ensure DB was not modified"):
            mono_env["uow"].transactions.bulk_insert_transactions.assert_not_called()

    @allure.title("Automatically create 'Uncategorized' category for new income")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_sync_tx_creates_uncat_and_maps_income(self, mono_env, app):
        with allure.step(
            "Arrange: Mock income transaction and missing default category"
        ):
            INCOME_TX = [
                {
                    "id": "mono_income_1",
                    "amount": 15000,
                    "description": "Salary",
                    "time": 1700000000,
                    "mcc": 1234,
                }
            ]
            mono_env["client"].get_transactions.return_value = INCOME_TX
            mono_env["uow"].categories.get_by_name_and_user.return_value = None

            fake_new_cat = Category(id=999, name="Uncategorized")
            mono_env["uow"].categories.create_category.return_value = fake_new_cat
            mono_env["uow"].transactions.bulk_insert_transactions.return_value = 1
            service = MonobankService(mono_env["uow"])

        with allure.step("Act: Call sync_tx"):
            with app.app_context():
                service.sync_tx(user_id=1)

        with allure.step("Assert: Verify category creation and income mapping"):
            mono_env["uow"].categories.create_category.assert_called_once_with(
                1, {"name": "Uncategorized"}
            )
            transactions_saved = mono_env[
                "uow"
            ].transactions.bulk_insert_transactions.call_args[0][0]
            assert transactions_saved[0].transaction_type == "income"
            assert transactions_saved[0].amount == Decimal("150.00")

    @allure.title("Sync successfully flushes DB and registers commit hooks")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_sync_tx_flushes_and_registers_hooks(self, mono_env, app):
        with allure.step("Arrange: Mock valid transactions and bulk insert"):
            mono_env["client"].get_transactions.return_value = FAKE_MONO_TRANSACTIONS
            mono_env["uow"].transactions.bulk_insert_transactions.return_value = 2
            service = MonobankService(mono_env["uow"])

        with allure.step("Act: Call sync_tx"):
            with app.app_context():
                service.sync_tx(user_id=1)

        with allure.step(
            "Assert: Verify flush and commit hooks (update_real_balance, recalculate_initial_point)"
        ):
            mono_env["uow"].flush.assert_called()
            mono_env["uow"].commit.assert_not_called()
            mono_env["uow"].profile.update_real_balance.assert_called_once()
            mono_env["profile_svc"].recalculate_initial_point.assert_called_once()
            assert mono_env["uow"].on_commit.call_count == 3

    @allure.title("Correctly select the 'black' UAH card from multiple accounts")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_card_stats_selects_black_uah_card(self, mono_env, app):
        with allure.step(
            "Arrange: Mock multiple accounts with different currencies and types"
        ):
            MULTI_CARDS_INFO = {
                "accounts": [
                    {
                        "id": "USD_CARD",
                        "type": "black",
                        "currencyCode": 840,
                        "balance": 5000,
                    },
                    {
                        "id": "WHITE_CARD",
                        "type": "white",
                        "currencyCode": 980,
                        "balance": 1000,
                    },
                    {
                        "id": "BLACK_UAH",
                        "type": "black",
                        "currencyCode": 980,
                        "balance": 99900,
                    },
                ]
            }
            mono_env["client"].get_client_info.return_value = MULTI_CARDS_INFO
            mono_env["client"].get_transactions.return_value = []
            service = MonobankService(mono_env["uow"])

        with allure.step("Act: Call sync_tx"):
            with app.app_context():
                service.sync_tx(user_id=1)

        with allure.step(
            "Assert: Verify the target card ID used for transaction fetch"
        ):
            mono_env["client"].get_transactions.assert_called_once()
            args = mono_env["client"].get_transactions.call_args[0]
            assert args[0] == "BLACK_UAH"

    @allure.title("Sync fails when Monobank returns no accounts")
    @allure.severity(allure.severity_level.NORMAL)
    def test_sync_tx_no_accounts_found(self, mono_env, app):
        with allure.step("Arrange: Mock empty accounts array"):
            mono_env["client"].get_client_info.return_value = {"accounts": []}
            service = MonobankService(mono_env["uow"])

        with allure.step("Act & Assert: Expect BusinessLogicError"):
            with pytest.raises(
                BusinessLogicError, match="No accounts found in Monobank"
            ):
                with app.app_context():
                    service.sync_tx(user_id=1)

    @allure.title("Sync fails on Forbidden Error (invalid/expired X-Token)")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_sync_tx_forbidden_error_from_api(self, mono_env, app):
        with allure.step("Arrange: Mock API error response for unknown token"):
            mono_env["client"].get_client_info.return_value = {
                "errorDescription": "Unknown 'X-Token'"
            }
            service = MonobankService(mono_env["uow"])

        with allure.step("Act & Assert: Expect ForbiddenError"):
            with pytest.raises(ForbiddenError, match="Unknown 'X-Token'"):
                with app.app_context():
                    service.sync_tx(user_id=1)
