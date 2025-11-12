from backend.finmate.transactions.repository import TransactionRepository
from datetime import date



class TransactionService:

    def __init__(self):
        self.repo = TransactionRepository()


    def create_transaction(self, data, user_id):

        if not data.get('amount'):
            raise ValueError("Amount is a required field.")

        if not data.get('transaction_type') or data.get('transaction_type') not in ['income', 'expense']:
            raise ValueError("Type must be 'income' or 'expense'.")

        if not data.get('title'):
            raise ValueError("Title is required.")

        data['user_id'] = user_id

        if not data.get('created_at'):
            data['created_at'] = date.today()


        new_tx = self.repo.create_transaction(data)

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

        if 'amount' in data and not data['amount']:
            raise ValueError("Amount cannot be empty.")
        if 'title' in data and not data['title']:
            raise ValueError("Title cannot be empty.")

        #TODO: DOPISAT!!

        updated_tx = self.repo.update_transaction(tx_to_update, data)
        return updated_tx


    def get_transaction(self, tx_id, user_id):
        transaction = self.repo.get_by_id(tx_id)

        if transaction.user_id != int(user_id):
            raise PermissionError("You are not authorized to view this transaction.")

        if not transaction:
            raise ValueError(f"Transaction with id {tx_id} not found.")

        return transaction