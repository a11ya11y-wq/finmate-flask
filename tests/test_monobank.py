from decimal import Decimal

import pytest
import requests

from finmate.monobank.service import MonobankService
from finmate.models import Users, Category
from finmate.exceptions import ThrottlingError
from finmate.exceptions import BusinessLogicError





FAKE_CLIENT_INFO = {"accounts": [{"id": "ACC_ID_001", 'type': 'black', 'balance': '10000000'}]}
FAKE_MONO_TRANSACTIONS = [
    {"id": "mono_id_NEW_1", "amount": 10000, "description": "Sushi", "time": 1700000000, "mcc": 5812},
    {"id": "mono_id_OLD_2", "amount": 5000, "description": "Rent", "time": 1700000000, "mcc": 4900},
]
FAKE_UNCAT_CATEGORY = Category(id=100, name="Uncategorized")
FAKE_USER = Users(id=1, monobank_api_token=b'FAKE_TOKEN')


def setup_mocks(mocker):
    mock_mono_client = mocker.patch(
        "finmate.monobank.service.MonoAPI",
        autospec=True
    ).return_value
    mock_mono_client.get_client_info.return_value = FAKE_CLIENT_INFO

    mock_profile_repo = mocker.patch(
        "finmate.monobank.service.ProfileRepository",
        autospec=True
    ).return_value
    mock_profile_repo.get_user_info.return_value = FAKE_USER

    mock_profile_service = mocker.patch(
        "finmate.monobank.service.ProfileService",
        autospec=True
    ).return_value
    mock_profile_service.recalculate_initial_point.return_value = 1000

    mock_cat_repo = mocker.patch(
        "finmate.monobank.service.CategoryRepository",
        autospec=True
    ).return_value
    mock_cat_repo.get_by_name_and_user.return_value = FAKE_UNCAT_CATEGORY

    mock_tx_repo = mocker.patch(
        "finmate.monobank.service.TransactionRepository",
        autospec=True
    ).return_value

    return mock_mono_client, mock_tx_repo, mock_cat_repo, mock_profile_repo


def test_sync_tx_success(mocker, app):
    mock_mono_client, mock_tx_repo, _, _ = setup_mocks(mocker)

    mock_mono_client.get_transactions.return_value = FAKE_MONO_TRANSACTIONS

    mock_tx_repo.get_existing_mono_ids.return_value = {"mono_id_OLD_2"}

    mock_tx_repo.bulk_insert_transactions.return_value = 1

    service = MonobankService()

    with app.app_context():
        added_count = service.sync_tx(user_id=1)

    assert added_count == 1

    mock_tx_repo.bulk_insert_transactions.assert_called_once()

    transactions_saved = mock_tx_repo.bulk_insert_transactions.call_args[0][0]

    assert len(transactions_saved) == 1
    saved_tx = transactions_saved[0]

    assert saved_tx.amount == Decimal('100.00')
    assert saved_tx.mono_id == "mono_id_NEW_1"


def test_sync_tx_fails_on_rate_limit(mocker, app):
    mock_mono_client, mock_tx_repo, mock_cat_repo, mock_profile_repo = setup_mocks(mocker)

    RATE_LIMIT_ERROR = {"errorDescription": "Too many requests", "status_code": 429}
    mock_mono_client.get_transactions.return_value = RATE_LIMIT_ERROR
    mock_cat_repo.get_all_categories.return_value = []

    service = MonobankService()

    with pytest.raises(ThrottlingError) as excinfo:
        with app.app_context():
            service.sync_tx(user_id=1)

    assert "Too many requests" in str(excinfo.value)

    mock_tx_repo.bulk_insert_transactions.assert_not_called()
    mock_tx_repo.get_existing_mono_ids.assert_not_called()


def test_sync_tx_no_new_tx(mocker, app):
    mock_mono_client , mock_tx_repo, mock_cat_repo, mock_profile_repo = setup_mocks(mocker)

    mock_mono_client.get_transactions.return_value = {}
    mock_tx_repo.bulk_insert_transactions.return_value = 0

    service = MonobankService()

    with app.app_context():
        added_count = service.sync_tx(user_id=1)

    assert added_count == 0
    mock_tx_repo.bulk_insert_transactions.assert_not_called()

def test_sync_tx_api_error(mocker, app):
    mock_mono_client, mock_tx_repo, mock_cat_repo, mock_profile_repo = setup_mocks(mocker)
    mock_mono_client.get_transactions.side_effect = requests.RequestException("Monobank is down")

    service = MonobankService()

    with pytest.raises(requests.RequestException):
        with app.app_context():
            service.sync_tx(user_id=1)

    mock_tx_repo.bulk_insert_transactions.assert_not_called()


def test_sync_tx_token_error(mocker, app):
    mock_mono_client, mock_tx_repo, mock_cat_repo, mock_profile_repo = setup_mocks(mocker)

    no_token_user = Users(id=1, monobank_api_token=None)
    mock_profile_repo.get_user_info.return_value = no_token_user

    service = MonobankService()

    with pytest.raises(BusinessLogicError, match="API token not found or user access denied."):
        with app.app_context():
            service.sync_tx(user_id=1)

    mock_tx_repo.bulk_insert_transactions.assert_not_called()