from decimal import Decimal

import pytest

from backend.finmate.monobank.service import MonobankService
from backend.finmate.models import Users, Category





FAKE_CLIENT_INFO = {"accounts": [{"id": "ACC_ID_001"}]}
FAKE_MONO_TRANSACTIONS = [
    {"id": "mono_id_NEW_1", "amount": 10000, "description": "Sushi", "time": 1700000000, "mcc": 5812},
    {"id": "mono_id_OLD_2", "amount": 5000, "description": "Rent", "time": 1700000000, "mcc": 4900},
]
FAKE_UNCAT_CATEGORY = Category(id=100, name="Uncategorized")
FAKE_USER = Users(id=1, monobank_api_token=b'FAKE_TOKEN')


def test_sync_tx_success(mocker, app):

    mock_mono_client = mocker.patch(
        "backend.finmate.monobank.service.MonoAPI",
        autospec=True
    )
    mock_mono_client.return_value.get_client_info.return_value = FAKE_CLIENT_INFO
    mock_mono_client.return_value.get_transactions.return_value = FAKE_MONO_TRANSACTIONS

    mock_profile_repo = mocker.patch(
        "backend.finmate.monobank.service.ProfileRepository",
        autospec=True
    ).return_value
    mock_profile_repo.get_user_info.return_value = FAKE_USER

    mock_cat_repo = mocker.patch(
        "backend.finmate.monobank.service.CategoryRepository",
        autospec=True
    ).return_value
    mock_cat_repo.get_by_name_and_user.return_value = FAKE_UNCAT_CATEGORY
    mock_cat_repo.get_all_categories.return_value = []

    mock_tx_repo = mocker.patch(
        "backend.finmate.monobank.service.TransactionRepository",
        autospec=True
    ).return_value
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
    assert saved_tx.title == "Sushi"
    assert saved_tx.mono_id == "mono_id_NEW_1"
    assert saved_tx.amount == Decimal('100.00')
    assert saved_tx.category_id == FAKE_UNCAT_CATEGORY.id
    assert saved_tx.transaction_type == 'income'