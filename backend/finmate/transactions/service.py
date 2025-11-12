from datetime import date

from pydantic import ValidationError

from backend.finmate.transactions.repository import TransactionRepository
from .schemas import TransactionCreateSchema, TransactionUpdateSchema




class TransactionService:

    def __init__(self):
        self.repo = TransactionRepository()


    def create_transaction(self, data, user_id):

        try:
            validated_data =TransactionCreateSchema.model_validate(data)
        except ValidationError as e:
            raise ValueError(e.errors())

        payload = validated_data.model_dump()
        payload['user_id'] = user_id

        new_tx = self.repo.create_transaction(payload)

        return new_tx


    def delete_transaction(self, tx_id, user_id):
        tx_to_delete = self.repo.get_by_id(tx_id)

        if not tx_to_delete:
            raise ValueError(f"Transaction with id {tx_id} not found.")

        if tx_to_delete.user_id != int(user_id):
            raise PermissionError("You are not authorized to delete this transaction.")

        self.repo.delete_transaction(tx_to_delete)

        return True


    def update_transaction(self, tx_id, user_id, data):
        tx_to_update = self.repo.get_by_id(tx_id)

        if not tx_to_update:
            raise ValueError(f"Transaction with id {tx_id} not found.")
        if tx_to_update.user_id != int(user_id):
            raise PermissionError("You are not authorized to edit this transaction.")

        try:
            validated_data  = TransactionUpdateSchema.model_validate(data)
        except ValidationError as e:
            raise ValueError(e.errors())

        update_payload = validated_data.model_dump(exclude_unset=True) #включи до нього ТІЛЬКИ ті поля, які користувач РЕАЛЬНО надіслав

        if not update_payload:
            raise ValueError("No valid fields to update.")

        updated_tx = self.repo.update_transaction(tx_to_update, update_payload)
        return updated_tx


    def get_transaction(self, tx_id, user_id):
        transaction = self.repo.get_by_id(tx_id)

        if not transaction:
            raise ValueError(f"Transaction with id {tx_id} not found.")

        if transaction.user_id != int(user_id):
            raise PermissionError("You are not authorized to view this transaction.")

        return transaction