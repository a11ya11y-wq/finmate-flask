from datetime import datetime, timezone
from unittest.mock import MagicMock

import allure
import pytest
from core_service.exceptions import BusinessLogicError, ResourceNotFound
from core_service.transactions.service import TransactionService
from pydantic import ValidationError


@pytest.fixture
@allure.title("Initialize Mocked Transaction UOW")
def transaction_uow():
    with allure.step("Initialize MagicMock for Transaction Unit of Work"):
        mock_uow = MagicMock()
        mock_uow.categories.get_cat_by_id_and_user.return_value = MagicMock(
            id=1, name="Test Category"
        )
        return mock_uow


SUCCESSFUL_TX_DATA = {
    "amount": 1000,
    "title": "Test Tx",
    "transaction_type": "expense",
    "category_id": 1,
}


@allure.feature("Transaction Management")
@allure.story("Retrieve Transaction")
class TestGetTransaction:

    @allure.title("Successfully retrieve a transaction by ID")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_get_transaction_by_id_success(self, transaction_uow):
        """Successful retrieval of a transaction by ID"""
        with allure.step("Arrange: Mock existing transaction"):
            transaction_uow.transactions.get_by_id_and_user.return_value = (
                SUCCESSFUL_TX_DATA
            )
            service = TransactionService(transaction_uow)

        with allure.step("Act: Fetch transaction"):
            result = service.get_transaction(tx_id=1, user_id=142)

        with allure.step("Assert: Verify payload"):
            transaction_uow.transactions.get_by_id_and_user.assert_called_once_with(
                142, 1
            )
            assert result == SUCCESSFUL_TX_DATA

    @allure.title("Fail to retrieve non-existent transaction")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_transaction_by_id_not_found(self, transaction_uow):
        """Transaction not found or access denied."""
        with allure.step("Arrange: Mock transaction not found"):
            transaction_uow.transactions.get_by_id_and_user.return_value = None
            service = TransactionService(transaction_uow)

        with allure.step("Act & Assert: Expect ResourceNotFound"):
            with pytest.raises(
                ResourceNotFound, match="Transaction 1 not found or access denied."
            ):
                service.get_transaction(tx_id=1, user_id=125)

        with allure.step("Assert: Verify DB query was made"):
            transaction_uow.transactions.get_by_id_and_user.assert_called_once_with(
                125, 1
            )


@allure.feature("Transaction Management")
@allure.story("Create Transaction")
class TestCreateTransaction:

    @allure.title("Successfully create a manual transaction")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_create_transaction_success(self, transaction_uow):
        """Successful transaction creation"""
        with allure.step("Arrange: Initialize service"):
            service = TransactionService(transaction_uow)

        with allure.step("Act: Call create_transaction"):
            service.create_transaction(user_id=12, data=SUCCESSFUL_TX_DATA)

        with allure.step("Assert: Verify payload mapped correctly and DB flushed"):
            transaction_uow.categories.get_cat_by_id_and_user.assert_called_once_with(
                1, 12
            )

            args, kwargs = transaction_uow.transactions.create_transaction.call_args
            actual_payload = args[0]
            assert actual_payload["amount"] == SUCCESSFUL_TX_DATA["amount"]
            assert actual_payload["title"] == SUCCESSFUL_TX_DATA["title"]
            assert (
                actual_payload["transaction_type"]
                == SUCCESSFUL_TX_DATA["transaction_type"]
            )
            assert actual_payload["category_id"] == SUCCESSFUL_TX_DATA["category_id"]
            assert actual_payload["user_id"] == 12
            assert "created_at" in actual_payload
            transaction_uow.flush.assert_called_once()

    @allure.title("Fail creation if assigned category is missing")
    @allure.severity(allure.severity_level.NORMAL)
    def test_create_transaction_category_not_found(self, transaction_uow):
        """Category not found or access denied"""
        with allure.step("Arrange: Mock category missing"):
            transaction_uow.categories.get_cat_by_id_and_user.return_value = None
            service = TransactionService(transaction_uow)

        with allure.step("Act & Assert: Expect ResourceNotFound"):
            with pytest.raises(
                ResourceNotFound, match="Category 1 not found or access denied."
            ):
                service.create_transaction(user_id=12, data=SUCCESSFUL_TX_DATA)

        with allure.step("Assert: Ensure transaction was not created"):
            transaction_uow.categories.get_cat_by_id_and_user.assert_called_once_with(
                1, 12
            )
            transaction_uow.transactions.create_transaction.assert_not_called()
            transaction_uow.flush.assert_not_called()

    @allure.title("Validation errors on invalid transaction payloads")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize(
        "invalid_data",
        [
            {},  # Empty data
            SUCCESSFUL_TX_DATA | {"amount": -100},  # Negative amount
            SUCCESSFUL_TX_DATA | {"title": ""},  # Empty title
            SUCCESSFUL_TX_DATA
            | {"transaction_type": "invalid_type"},  # Invalid transaction type
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
            SUCCESSFUL_TX_DATA
            | {"amount": 0},  # Zero amount (should be invalid due to gt=0)
            SUCCESSFUL_TX_DATA
            | {"amount": -0.01},  # Negative amount (should be invalid due to gt=0)
            SUCCESSFUL_TX_DATA | {"amount": 100.999},  # More than 2 decimal places
            SUCCESSFUL_TX_DATA | {"amount": 100000000000},  # More than max digits
            SUCCESSFUL_TX_DATA
            | {"created_at": "2024-13-01T00:00:00Z"},  # Invalid month in datetime
            SUCCESSFUL_TX_DATA
            | {"created_at": "2024-00-01T00:00:00Z"},  # Invalid month in datetime
            SUCCESSFUL_TX_DATA
            | {"created_at": "2024-01-32T00:00:00Z"},  # Invalid day in datetime
            SUCCESSFUL_TX_DATA
            | {"created_at": "2024-01-01T25:00:00Z"},  # Invalid hour in datetime
            SUCCESSFUL_TX_DATA
            | {"created_at": "2024-01-01T00:60:00Z"},  # Invalid minute in datetime
            SUCCESSFUL_TX_DATA
            | {"created_at": "2024-01-01T00:00:60Z"},  # Invalid second in datetime
            SUCCESSFUL_TX_DATA
            | {"created_at": "02-30-2024T00:00:00Z"},  # Invalid date format
            SUCCESSFUL_TX_DATA
            | {"created_at": "2024/01/01T00:00:00Z"},  # Invalid date format
        ],
    )
    def test_create_transaction_invalid_data(self, transaction_uow, invalid_data):
        """Validation error for invalid input data"""
        with allure.step("Arrange: Initialize service"):
            service = TransactionService(transaction_uow)

        with allure.step("Act & Assert: Expect ValidationError"):
            with pytest.raises(ValidationError):
                service.create_transaction(user_id=121, data=invalid_data)

        with allure.step("Assert: Ensure DB was not modified"):
            transaction_uow.categories.get_cat_by_id_and_user.assert_not_called()
            transaction_uow.transactions.create_transaction.assert_not_called()
            transaction_uow.flush.assert_not_called()


@allure.feature("Transaction Management")
@allure.story("Delete Transaction")
class TestDeleteTransaction:

    @allure.title("Successfully delete a manual transaction")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_transaction_success(self, transaction_uow):
        """Successful transaction deletion"""
        with allure.step("Arrange: Mock manual transaction (mono_id=None)"):
            transaction_uow.transactions.get_by_id_and_user.return_value = MagicMock(
                id=1, mono_id=None
            )
            service = TransactionService(transaction_uow)

        with allure.step("Act: Call delete_transaction"):
            service.delete_transaction(tx_id=1, user_id=132)

        with allure.step("Assert: Verify deletion method was called"):
            transaction_uow.transactions.get_by_id_and_user.assert_called_once_with(
                132, 1
            )
            transaction_uow.transactions.delete_transaction.assert_called_once()

    @allure.title("Fail to delete non-existent transaction")
    @allure.severity(allure.severity_level.NORMAL)
    def test_delete_transaction_not_found(self, transaction_uow):
        """Transaction not found or access denied"""
        with allure.step("Arrange: Mock missing transaction"):
            transaction_uow.transactions.get_by_id_and_user.return_value = None
            service = TransactionService(transaction_uow)

        with allure.step("Act & Assert: Expect ResourceNotFound"):
            with pytest.raises(
                ResourceNotFound, match="Transaction 1 not found or access denied."
            ):
                service.delete_transaction(tx_id=1, user_id=122)

        with allure.step("Assert: Ensure delete was not called"):
            transaction_uow.transactions.get_by_id_and_user.assert_called_once_with(
                122, 1
            )
            transaction_uow.transactions.delete_transaction.assert_not_called()

    @allure.title("Fail to delete a synchronized bank transaction")
    @allure.severity(allure.severity_level.NORMAL)
    def test_delete_transaction_mono_id_present(self, transaction_uow):
        """Cannot delete a synchronized bank transaction"""
        with allure.step("Arrange: Mock synchronized transaction (mono_id present)"):
            transaction_uow.transactions.get_by_id_and_user.return_value = MagicMock(
                id=1, mono_id="mono_123"
            )
            service = TransactionService(transaction_uow)

        with allure.step("Act & Assert: Expect BusinessLogicError"):
            with pytest.raises(
                BusinessLogicError,
                match="You cannot delete a synchronized bank transaction.",
            ):
                service.delete_transaction(tx_id=1, user_id=122)

        with allure.step("Assert: Ensure delete was not called"):
            transaction_uow.transactions.get_by_id_and_user.assert_called_once_with(
                122, 1
            )
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


@allure.feature("Transaction Management")
@allure.story("Update Transaction")
class TestUpdateTransaction:

    @allure.title("Successfully update non-synchronized transaction fields")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize(
        "update_data",
        [
            {
                "title": "New Title",
                "amount": 750,
                "transaction_type": "income",
                "category_id": 2,
                "created_at": "2024-02-01T00:00:00Z",
                "note": "New Note",
            },
            {
                "title": "Updated Title",
                "note": "Updated Note",
            },  # Partial update - only title and note
            {
                "amount": 250,
                "transaction_type": "expense",
            },  # Partial update - only amount and transaction_type
            {"created_at": "2026-05-26"},  # Partial update - only created_at
            {
                "created_at": "2026-05-26T15:30:00Z"
            },  # Partial update - only created_at with time
            {
                "created_at": datetime(2026, 5, 26, 15, 30, tzinfo=timezone.utc)
            },  # Partial update - only created_at with datetime object
            {"note": "Just a note update"},  # Partial update - only note
            {"title": "Another Title"},  # Partial update - only title
            {"amount": 999},  # Partial update - only amount
            {"transaction_type": "income"},  # Partial update - only transaction_type
            {"category_id": 4},  # Partial update - only category_id
        ],
    )
    def test_update_nonsync_transaction_success(self, transaction_uow, update_data):
        """Successful non-synchronized transaction update"""
        with allure.step("Arrange: Mock existing non-sync transaction"):
            transaction_uow.transactions.get_by_id_and_user.return_value = MagicMock(
                **EXISTING_TX_DATA
            )
            service = TransactionService(transaction_uow)

        with allure.step("Act: Update transaction"):
            service.update_transaction(tx_id=1, user_id=132, data=update_data)

        with allure.step("Assert: Verify payload matches update data"):
            transaction_uow.transactions.get_by_id_and_user.assert_called_once_with(
                132, 1
            )
            args, kwargs = transaction_uow.transactions.update_transaction.call_args
            update_payload = args[1]

            for field in update_data:
                assert field in update_payload
                if field == "created_at":
                    actual_date = update_payload[field].date()
                    if isinstance(update_data[field], str):
                        expected_date = datetime.fromisoformat(
                            update_data[field].replace("Z", "+00:00")
                        ).date()
                    else:
                        expected_date = update_data[field].date()
                    assert (
                        actual_date == expected_date
                    ), f"Expected date {expected_date}, got {actual_date}"
                else:
                    assert update_payload[field] == update_data[field]

    @allure.title(
        "Update allowed fields (category/note) for a synchronized transaction"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize(
        "update_data",
        [
            {"category_id": 2, "note": "Updated Note for Mono Tx"},  # Allowed fields
            {"category_id": 3},  # Only category_id
            {"note": "Only note update"},  # Only note
        ],
    )
    def test_update_synchronized_transaction_success(
        self, transaction_uow, update_data
    ):
        """Successful update of allowed fields for a synchronized transaction"""
        with allure.step("Arrange: Mock synchronized transaction"):
            transaction_uow.transactions.get_by_id_and_user.return_value = MagicMock(
                **EXISTING_TX_DATA | {"mono_id": "mono_123"}
            )
            service = TransactionService(transaction_uow)

        with allure.step("Act: Update allowed fields"):
            service.update_transaction(tx_id=1, user_id=1132, data=update_data)

        with allure.step("Assert: Verify updated allowed fields"):
            transaction_uow.transactions.get_by_id_and_user.assert_called_once_with(
                1132, 1
            )
            args, kwargs = transaction_uow.transactions.update_transaction.call_args
            update_payload = args[1]

            assert update_payload.get(
                "category_id", EXISTING_TX_DATA["category_id"]
            ) == update_data.get("category_id", EXISTING_TX_DATA["category_id"])
            assert update_payload.get(
                "note", EXISTING_TX_DATA["note"]
            ) == update_data.get("note", EXISTING_TX_DATA["note"])

    @allure.title("Fail to update forbidden fields for a synchronized transaction")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize(
        "update_data",
        [
            {"amount": 750},
            {"transaction_type": "income"},
            {"created_at": "2024-02-01T00:00:00Z"},
            {"created_at": datetime(2024, 2, 1, tzinfo=timezone.utc)},
            {"amount": 750, "transaction_type": "income"},
            {"amount": 750, "created_at": "2024-02-01T00:00:00Z"},
            {"transaction_type": "income", "created_at": "2024-02-01T00:00:00Z"},
            {
                "amount": 750,
                "transaction_type": "income",
                "created_at": "2024-02-01T00:00:00Z",
            },
            {
                "title": "New Title",
                "amount": 750,
                "transaction_type": "income",
                "created_at": "2024-02-01T00:00:00Z",
            },
            {
                "title": "New Title",
                "amount": 750,
                "transaction_type": "income",
                "created_at": datetime(2024, 2, 1, tzinfo=timezone.utc),
            },
        ],
    )
    def test_update_synchronized_transaction_forbidden_fields(
        self, transaction_uow, update_data
    ):
        """Attempting to update forbidden fields of a synchronized transaction"""
        with allure.step("Arrange: Mock synchronized transaction"):
            transaction_uow.transactions.get_by_id_and_user.return_value = MagicMock(
                **EXISTING_TX_DATA | {"mono_id": "mono_123"}
            )
            service = TransactionService(transaction_uow)

        with allure.step("Act & Assert: Expect BusinessLogicError"):
            with pytest.raises(
                BusinessLogicError,
                match="You can only change the category and notes for a bank transaction.",
            ):
                service.update_transaction(tx_id=1, user_id=132, data=update_data)

        with allure.step("Assert: Ensure update was not called"):
            transaction_uow.transactions.get_by_id_and_user.assert_called_once_with(
                132, 1
            )
            transaction_uow.transactions.update_transaction.assert_not_called()

    @allure.title("Fail to update non-existent transaction")
    @allure.severity(allure.severity_level.NORMAL)
    def test_update_transaction_not_found(self, transaction_uow):
        """Transaction not found or access denied"""
        with allure.step("Arrange: Mock transaction not found"):
            transaction_uow.transactions.get_by_id_and_user.return_value = None
            service = TransactionService(transaction_uow)

        with allure.step("Act & Assert: Expect ResourceNotFound"):
            with pytest.raises(
                ResourceNotFound, match="Transaction 1 not found or access denied."
            ):
                service.update_transaction(
                    tx_id=1, user_id=132, data={"title": "New Title"}
                )

        with allure.step("Assert: Ensure update was not called"):
            transaction_uow.transactions.get_by_id_and_user.assert_called_once_with(
                132, 1
            )
            transaction_uow.transactions.update_transaction.assert_not_called()

    @allure.title("Fail update if payload is empty")
    @allure.severity(allure.severity_level.NORMAL)
    def test_update_transaction_no_valid_changes(self, transaction_uow):
        """No valid changes detected in the update payload"""
        with allure.step("Arrange: Mock existing transaction"):
            transaction_uow.transactions.get_by_id_and_user.return_value = MagicMock(
                **EXISTING_TX_DATA
            )
            service = TransactionService(transaction_uow)

        with allure.step("Act & Assert: Expect BusinessLogicError on empty payload"):
            with pytest.raises(BusinessLogicError, match="No valid fields to update."):
                service.update_transaction(tx_id=1, user_id=132, data={})

        with allure.step("Assert: Ensure DB was not queried"):
            transaction_uow.transactions.get_by_id_and_user.assert_not_called()
            transaction_uow.transactions.update_transaction.assert_not_called()

    @allure.title("Fail update if assigned category does not exist")
    @allure.severity(allure.severity_level.NORMAL)
    def test_update_transaction_category_not_found(self, transaction_uow):
        """Category not found or access denied during transaction update"""
        with allure.step("Arrange: Mock existing transaction and missing category"):
            transaction_uow.transactions.get_by_id_and_user.return_value = MagicMock(
                **EXISTING_TX_DATA
            )
            transaction_uow.categories.get_cat_by_id_and_user.return_value = None
            service = TransactionService(transaction_uow)

        with allure.step("Act & Assert: Expect ResourceNotFound"):
            with pytest.raises(
                ResourceNotFound, match="Category 999 not found or access denied."
            ):
                service.update_transaction(
                    tx_id=1, user_id=132, data={"category_id": 999}
                )

        with allure.step("Assert: Verify DB interactions stopped"):
            transaction_uow.transactions.get_by_id_and_user.assert_called_once_with(
                132, 1
            )
            transaction_uow.categories.get_cat_by_id_and_user.assert_called_once_with(
                999, 132
            )
            transaction_uow.transactions.update_transaction.assert_not_called()

    @allure.title("Validation errors on invalid transaction fields during update")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize(
        "update_data",
        [
            {"amount": -100},  # Negative amount
            {"transaction_type": "invalid_type"},  # Invalid transaction type
            {"category_id": "not_an_int"},  # Invalid category_id
            {"amount": 100.123},  # More than 2 decimal places
            {"amount": 10000000000},  # More than max digits
            {"note": "x" * 129},  # Note too long
            {"created_at": "not_a_datetime"},  # Invalid datetime
            {"title": "x" * 51},  # Title too long
            {"amount": "not_a_decimal"},  # Invalid decimal
            {"amount": 0},  # Zero amount (should be invalid due to gt=0)
            {"amount": -0.01},  # Negative amount (should be invalid due to gt=0)
        ],
    )
    def test_update_transaction_invalid_data(self, transaction_uow, update_data):
        """Validation error for invalid input data during transaction update"""
        with allure.step("Arrange: Initialize service"):
            transaction_uow.transactions.get_by_id_and_user.return_value = MagicMock(
                **EXISTING_TX_DATA
            )
            service = TransactionService(transaction_uow)

        with allure.step("Act & Assert: Expect ValidationError"):
            with pytest.raises(ValidationError):
                service.update_transaction(tx_id=1, user_id=132, data=update_data)

        with allure.step("Assert: Ensure DB was not modified"):
            transaction_uow.transactions.get_by_id_and_user.assert_not_called()
            transaction_uow.transactions.update_transaction.assert_not_called()

    @allure.title("Fail update if payload contains empty/None values")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize(
        "update_data",
        [
            {"amount": None},
            {"category_id": None},
            {"transaction_type": None},
            {"title": None},
            {"created_at": None},
            {},
        ],
    )
    def test_update_transaction_empty_data_errors(self, transaction_uow, update_data):
        with allure.step("Arrange: Mock existing transaction"):
            transaction_uow.transactions.get_by_id_and_user.return_value = MagicMock(
                **EXISTING_TX_DATA
            )
            service = TransactionService(transaction_uow)

        with allure.step("Act & Assert: Expect BusinessLogicError"):
            with pytest.raises(BusinessLogicError, match="No valid fields to update"):
                service.update_transaction(tx_id=1, user_id=132, data=update_data)

        with allure.step("Assert: Ensure DB was not modified"):
            transaction_uow.transactions.get_by_id_and_user.assert_not_called()
            transaction_uow.transactions.update_transaction.assert_not_called()
            transaction_uow.flush.assert_not_called()
