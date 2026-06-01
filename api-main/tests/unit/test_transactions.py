from datetime import datetime, timezone

from pydantic import ValidationError
import pytest
from unittest.mock import MagicMock
from core_service.transactions.service import TransactionService
from core_service.exceptions import ResourceNotFound, BusinessLogicError


@pytest.fixture
def transaction_uow():
    mock_uow = MagicMock()
    mock_uow.categories.get_cat_by_id_and_user.return_value = MagicMock(id=1, name="Test Category")
    return mock_uow


SUCCESSFUL_TX_DATA = {
            "amount": 1000,
            "title": "Test Tx",
            "transaction_type": "expense",
            "category_id": 1,
        }


class TestGetTransaction:

    def test_get_transaction_by_id_success(self, transaction_uow):
        """Successful retrieval of a transaction by ID"""

        transaction_uow.transactions.get_by_id_and_user.return_value = SUCCESSFUL_TX_DATA

        service = TransactionService(transaction_uow)
        result = service.get_transaction(tx_id=1, user_id=142)

        transaction_uow.transactions.get_by_id_and_user.assert_called_once_with(142, 1)
        assert result == SUCCESSFUL_TX_DATA

    def test_get_transaction_by_id_not_found(self, transaction_uow):
        """Transaction not found or access denied."""

        transaction_uow.transactions.get_by_id_and_user.return_value = None

        service = TransactionService(transaction_uow)

        with pytest.raises(ResourceNotFound, match="Transaction 1 not found or access denied."):
            service.get_transaction(tx_id=1, user_id=125)

        transaction_uow.transactions.get_by_id_and_user.assert_called_once_with(125, 1)


class TestCreateTransaction:

    def test_create_transaction_success(self, transaction_uow):
        """Successful transaction creation"""

        service = TransactionService(transaction_uow)
        service.create_transaction(user_id=12, data=SUCCESSFUL_TX_DATA)

        transaction_uow.categories.get_cat_by_id_and_user.assert_called_once_with(1, 12)
        
        args, kwargs = transaction_uow.transactions.create_transaction.call_args

        actual_payload = args[0]
        assert actual_payload["amount"] == SUCCESSFUL_TX_DATA["amount"]
        assert actual_payload["title"] == SUCCESSFUL_TX_DATA["title"]
        assert actual_payload["transaction_type"] == SUCCESSFUL_TX_DATA["transaction_type"]
        assert actual_payload["category_id"] == SUCCESSFUL_TX_DATA["category_id"]
        assert actual_payload["user_id"] == 12
        assert "created_at" in actual_payload

        transaction_uow.flush.assert_called_once()

    def test_create_transaction_category_not_found(self, transaction_uow):
        """Category not found or access denied"""

        transaction_uow.categories.get_cat_by_id_and_user.return_value = None

        service = TransactionService(transaction_uow)

        with pytest.raises(ResourceNotFound, match="Category 1 not found or access denied."):
            service.create_transaction(user_id=12, data=SUCCESSFUL_TX_DATA)

        transaction_uow.categories.get_cat_by_id_and_user.assert_called_once_with(1, 12)
        transaction_uow.transactions.create_transaction.assert_not_called()
        transaction_uow.flush.assert_not_called()

    @pytest.mark.parametrize("invalid_data", [
        {},  # Empty data
        SUCCESSFUL_TX_DATA | {"amount": -100},  # Negative amount
        SUCCESSFUL_TX_DATA | {"title": ""},  # Empty title
        SUCCESSFUL_TX_DATA | {"transaction_type": "invalid_type"},  # Invalid transaction type
        SUCCESSFUL_TX_DATA | {"category_id": "not_an_int"},  # Invalid category_id
        SUCCESSFUL_TX_DATA | {"amount": 100.123},  # More than 2 decimal places
        SUCCESSFUL_TX_DATA | {"amount": 10000000000},  # More than max digits
        SUCCESSFUL_TX_DATA | {"note": "x" * 129},  # Note too long
        SUCCESSFUL_TX_DATA | {"created_at": "not_a_datetime"},  # Invalid datetime
        SUCCESSFUL_TX_DATA | {"title": "x" * 51},  # Title too long
        SUCCESSFUL_TX_DATA | {"amount": None},  # Null amount
        SUCCESSFUL_TX_DATA | {"category_id": None},  # Null category_id
        SUCCESSFUL_TX_DATA | {"transaction_type": None},  # Null transaction_type
        SUCCESSFUL_TX_DATA | {"title": None},  # Null title
        SUCCESSFUL_TX_DATA | {"created_at": None},  # Null created_at
        SUCCESSFUL_TX_DATA | {"amount": "not_a_decimal"},  # Invalid decimal
        SUCCESSFUL_TX_DATA | {"amount": 0},  # Zero amount (should be invalid due to gt=0)
        SUCCESSFUL_TX_DATA | {"amount": -0.01},  # Negative amount (should be invalid due to gt=0)
        SUCCESSFUL_TX_DATA | {"amount": 100.999},  # More than 2 decimal places
        SUCCESSFUL_TX_DATA | {"amount": 100000000000},  # More than max digits
        SUCCESSFUL_TX_DATA | {"created_at": "2024-13-01T00:00:00Z"},  # Invalid month in datetime
        SUCCESSFUL_TX_DATA | {"created_at": "2024-00-01T00:00:00Z"},  # Invalid month in datetime
        SUCCESSFUL_TX_DATA | {"created_at": "2024-01-32T00:00:00Z"},  # Invalid day in datetime
        SUCCESSFUL_TX_DATA | {"created_at": "2024-01-01T25:00:00Z"},  # Invalid hour in datetime
        SUCCESSFUL_TX_DATA | {"created_at": "2024-01-01T00:60:00Z"},  # Invalid minute in datetime
        SUCCESSFUL_TX_DATA | {"created_at": "2024-01-01T00:00:60Z"},  # Invalid second in datetime
        SUCCESSFUL_TX_DATA | {"created_at": "02-30-2024T00:00:00Z"},  # Invalid date format
        SUCCESSFUL_TX_DATA | {"created_at": "2024/01/01T00:00:00Z"},  # Invalid date format
    ])
    def test_create_transaction_invalid_data(self, transaction_uow, invalid_data):
        """Validation error for invalid input data"""

        service = TransactionService(transaction_uow)

        with pytest.raises(ValidationError):
            service.create_transaction(user_id=121, data=invalid_data)

        transaction_uow.categories.get_cat_by_id_and_user.assert_not_called()
        transaction_uow.transactions.create_transaction.assert_not_called()
        transaction_uow.flush.assert_not_called()

class TestDeleteTransaction:
    
    def test_delete_transaction_success(self, transaction_uow):
        """Successful transaction deletion"""

        transaction_uow.transactions.get_by_id_and_user.return_value = MagicMock(id=1, mono_id=None)

        service = TransactionService(transaction_uow)
        service.delete_transaction(tx_id=1, user_id=132)

        transaction_uow.transactions.get_by_id_and_user.assert_called_once_with(132, 1)
        transaction_uow.transactions.delete_transaction.assert_called_once()

    def test_delete_transaction_not_found(self, transaction_uow):
        """Transaction not found or access denied"""

        transaction_uow.transactions.get_by_id_and_user.return_value = None

        service = TransactionService(transaction_uow)

        with pytest.raises(ResourceNotFound, match="Transaction 1 not found or access denied."):
            service.delete_transaction(tx_id=1, user_id=122)

        transaction_uow.transactions.get_by_id_and_user.assert_called_once_with(122, 1)
        transaction_uow.transactions.delete_transaction.assert_not_called()

    def test_delete_transaction_mono_id_present(self, transaction_uow):
        """Cannot delete a synchronized bank transaction"""

        transaction_uow.transactions.get_by_id_and_user.return_value = MagicMock(id=1, mono_id="mono_123")

        service = TransactionService(transaction_uow)

        with pytest.raises(BusinessLogicError, match="You cannot delete a synchronized bank transaction."):
            service.delete_transaction(tx_id=1, user_id=122)

        transaction_uow.transactions.get_by_id_and_user.assert_called_once_with(122, 1)
        transaction_uow.transactions.delete_transaction.assert_not_called()



EXISTING_TX_DATA = {
    "id": 1,
    "transaction_type": "expense",
    "amount": 500,
    "title": "Old Title",
    "category_id": 1,
    "created_at": datetime(2024, 1, 1, tzinfo=timezone.utc),
    "note": "Old Note",
    "mono_id": None,
}
class TestUpdateTransaction:

    @pytest.mark.parametrize("update_data", [
        {
            "title": "New Title",
            "amount": 750,
            "transaction_type": "income",
            "category_id": 2,
            "created_at": "2024-02-01T00:00:00Z",
            "note": "New Note"
        },
        {
            # Partial update - only title and note
            "title": "Updated Title",
            "note": "Updated Note"
        },
        {
            # Partial update - only amount and transaction_type
            "amount": 250,
            "transaction_type": "expense"
        },
        {
            # Partial update - only created_at
            "created_at": "2026-05-26"
        },
        {
            # Partial update - only created_at with time
            "created_at": "2026-05-26T15:30:00Z"
        },
        {   # Partial update - only created_at with datetime object
            "created_at": datetime(2026, 5, 26, 15, 30, tzinfo=timezone.utc)
        },
        {
            # Partial update - only note
            "note": "Just a note update"
        },
        {
            # Partial update - only title
            "title": "Another Title"
        },
        {
            # Partial update - only amount
            "amount": 999
        },
        {
            # Partial update - only transaction_type
            "transaction_type": "income"
        },
        {
            # Partial update - only category_id
            "category_id": 4
        },
    ])
    def test_update_nonsync_transaction_success(self, transaction_uow, update_data):
        """Successful non-synchronized transaction update"""

        transaction_uow.transactions.get_by_id_and_user.return_value = MagicMock(**EXISTING_TX_DATA)

        service = TransactionService(transaction_uow)
        service.update_transaction(tx_id=1, user_id=132, data=update_data)

        transaction_uow.transactions.get_by_id_and_user.assert_called_once_with(132, 1)

        args, kwargs = transaction_uow.transactions.update_transaction.call_args

        update_payload = args[1]

        for field in update_data:
            assert field in update_payload
            
            if field == "created_at":
                actual_date = update_payload[field].date()

                if isinstance(update_data[field], str):
                    expected_date = datetime.fromisoformat(update_data[field].replace("Z", "+00:00")).date()
                else:
                    expected_date = update_data[field].date()
                    
                assert actual_date == expected_date, f"Expected date {expected_date}, got {actual_date}"
                
            else:
                assert update_payload[field] == update_data[field]


    @pytest.mark.parametrize("update_data", [
        { "category_id": 2, "note": "Updated Note for Mono Tx" },  # Allowed fields
        { "category_id": 3 },  # Only category_id
        { "note": "Only note update" },  # Only note
    ])
    def test_update_synchronized_transaction_success(self, transaction_uow, update_data):
        """Successful update of allowed fields for a synchronized transaction"""

        transaction_uow.transactions.get_by_id_and_user.return_value = MagicMock(**EXISTING_TX_DATA | {"mono_id": "mono_123"})

        service = TransactionService(transaction_uow)

        service.update_transaction(tx_id=1, user_id=1132, data=update_data)

        transaction_uow.transactions.get_by_id_and_user.assert_called_once_with(1132, 1)

        args, kwargs = transaction_uow.transactions.update_transaction.call_args
        update_payload = args[1]

        assert update_payload.get("category_id", EXISTING_TX_DATA["category_id"]) == update_data.get("category_id", EXISTING_TX_DATA["category_id"])
        assert update_payload.get("note", EXISTING_TX_DATA["note"]) == update_data.get("note", EXISTING_TX_DATA["note"])

    @pytest.mark.parametrize("update_data", [
        { "amount": 750 },
        { "transaction_type": "income" },
        { "created_at": "2024-02-01T00:00:00Z" },
        { "created_at": datetime(2024, 2, 1, tzinfo=timezone.utc) },
        { "amount": 750, "transaction_type": "income" },
        { "amount": 750, "created_at": "2024-02-01T00:00:00Z" },
        { "transaction_type": "income", "created_at": "2024-02-01T00:00:00Z" },
        { "amount": 750, "transaction_type": "income", "created_at": "2024-02-01T00:00:00Z" },
        { "title": "New Title", "amount": 750, "transaction_type": "income", "created_at": "2024-02-01T00:00:00Z" },
        { "title": "New Title", "amount": 750, "transaction_type": "income", "created_at": datetime(2024, 2, 1, tzinfo=timezone.utc) },
    ])
    def test_update_synchronized_transaction_forbidden_fields(self, transaction_uow, update_data):
        """Attempting to update forbidden fields of a synchronized transaction"""

        transaction_uow.transactions.get_by_id_and_user.return_value = MagicMock(**EXISTING_TX_DATA | {"mono_id": "mono_123"})

        service = TransactionService(transaction_uow)

        with pytest.raises(BusinessLogicError, match="You can only change the category and notes for a bank transaction."):
            service.update_transaction(tx_id=1, user_id=132, data=update_data)

        transaction_uow.transactions.get_by_id_and_user.assert_called_once_with(132, 1)
        transaction_uow.transactions.update_transaction.assert_not_called()

    def test_update_transaction_not_found(self, transaction_uow):
        """Transaction not found or access denied"""

        transaction_uow.transactions.get_by_id_and_user.return_value = None

        service = TransactionService(transaction_uow)

        with pytest.raises(ResourceNotFound, match="Transaction 1 not found or access denied."):
            service.update_transaction(tx_id=1, user_id=132, data={"title": "New Title"})

        transaction_uow.transactions.get_by_id_and_user.assert_called_once_with(132, 1)
        transaction_uow.transactions.update_transaction.assert_not_called()

    def test_update_transaction_no_valid_changes(self, transaction_uow):
        """No valid changes detected in the update payload"""

        transaction_uow.transactions.get_by_id_and_user.return_value = MagicMock(**EXISTING_TX_DATA)

        service = TransactionService(transaction_uow)

        with pytest.raises(BusinessLogicError, match="No valid fields to update."):
            service.update_transaction(tx_id=1, user_id=132, data={})

        transaction_uow.transactions.get_by_id_and_user.assert_not_called()  # Validation should fail before fetching the transaction
        transaction_uow.transactions.update_transaction.assert_not_called()

    def test_update_transaction_category_not_found(self, transaction_uow):
        """Category not found or access denied during transaction update"""

        transaction_uow.transactions.get_by_id_and_user.return_value = MagicMock(**EXISTING_TX_DATA)
        transaction_uow.categories.get_cat_by_id_and_user.return_value = None

        service = TransactionService(transaction_uow)

        with pytest.raises(ResourceNotFound, match="Category 999 not found or access denied."):
            service.update_transaction(tx_id=1, user_id=132, data={"category_id": 999})

        transaction_uow.transactions.get_by_id_and_user.assert_called_once_with(132, 1)
        transaction_uow.categories.get_cat_by_id_and_user.assert_called_once_with(999, 132)
        transaction_uow.transactions.update_transaction.assert_not_called()

    @pytest.mark.parametrize("update_data", [
        { "amount": -100 },  # Negative amount
        { "transaction_type": "invalid_type" },  # Invalid transaction type
        { "category_id": "not_an_int" },  # Invalid category_id
        { "amount": 100.123 },  # More than 2 decimal places
        { "amount": 10000000000 },  # More than max digits
        { "note": "x" * 129 },  # Note too long
        { "created_at": "not_a_datetime" },  # Invalid datetime
        { "title": "x" * 51 },  # Title too long
        { "amount": "not_a_decimal" },  # Invalid decimal
        { "amount": 0 },  # Zero amount (should be invalid due to gt=0)
        { "amount": -0.01 },  # Negative amount (should be invalid due to gt=0)
    ])
    def test_update_transaction_invalid_data(self, transaction_uow, update_data):
        """Validation error for invalid input data during transaction update"""

        transaction_uow.transactions.get_by_id_and_user.return_value = MagicMock(**EXISTING_TX_DATA)

        service = TransactionService(transaction_uow)

        with pytest.raises(ValidationError):
            service.update_transaction(tx_id=1, user_id=132, data=update_data)

        transaction_uow.transactions.get_by_id_and_user.assert_not_called()  # Validation should fail before fetching the transaction
        transaction_uow.transactions.update_transaction.assert_not_called()

    @pytest.mark.parametrize("update_data", [
        { "amount": None }, 
        { "category_id": None }, 
        { "transaction_type": None }, 
        { "title": None }, 
        { "created_at": None }, 
        {},
    ])
    def test_update_transaction_empty_data_errors(self, transaction_uow, update_data):
        transaction_uow.transactions.get_by_id_and_user.return_value = MagicMock(**EXISTING_TX_DATA)
        service = TransactionService(transaction_uow)

        with pytest.raises(BusinessLogicError, match="No valid fields to update"):
            service.update_transaction(tx_id=1, user_id=132, data=update_data)

        transaction_uow.transactions.get_by_id_and_user.assert_not_called()  
        transaction_uow.transactions.update_transaction.assert_not_called()
        transaction_uow.flush.assert_not_called()


