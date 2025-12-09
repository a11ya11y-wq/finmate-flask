from datetime import  datetime, time

from pydantic import ValidationError

from backend.finmate.transactions.repository import TransactionRepository
from backend.finmate.categories.repository import CategoryRepository
from .schemas import TransactionCreateSchema, TransactionUpdateSchema




class TransactionService:

    def __init__(self):
        self.repo = TransactionRepository()
        self.cat_repo = CategoryRepository()


    def create_transaction(self, data, user_id):

        try:
            validated_data = TransactionCreateSchema.model_validate(data)
        except ValidationError as e:
            raise ValueError(e.errors())

        category_id = validated_data.category_id

        cat_obj = self.cat_repo.get_by_id_and_user(category_id, user_id)

        if not cat_obj:
            raise PermissionError(f"Category {category_id} not found or access denied.")

        payload = validated_data.model_dump()
        payload['user_id'] = user_id

        new_tx = self.repo.create_transaction(payload)

        return new_tx


    def delete_transaction(self, tx_id, user_id):
        tx_to_delete = self.repo.get_by_id_and_user(user_id, tx_id)

        if not tx_to_delete:
            raise PermissionError(f"Transaction {tx_id} not found or access denied.")

        self.repo.delete_transaction(tx_to_delete)

        return True


    def update_transaction(self, tx_id, user_id, data):
        tx_to_update = self.repo.get_by_id_and_user(user_id, tx_id)

        if not tx_to_update:
            raise PermissionError(f"Transaction {tx_id} not found or access denied.")

        try:
            validated_data  = TransactionUpdateSchema.model_validate(data)
        except ValidationError as e:
            raise ValueError(e.errors())

        update_payload = validated_data.model_dump(exclude_unset=True) #включи до нього ТІЛЬКИ ті поля, які користувач РЕАЛЬНО надіслав

        if not update_payload:
            raise ValueError("No valid fields to update.")

        if 'category_id' in update_payload:
            new_cat_id = update_payload['category_id']
            cat_obj = self.cat_repo.get_by_id_and_user(new_cat_id, user_id)

            if not cat_obj:
                raise PermissionError(f"Category {new_cat_id} not found or access denied.")

        if 'created_at' in update_payload: # Додає час для дати (При редагуванні дати, час має залишатися той самий)
            new_date = update_payload['created_at']
            original_time = tx_to_update.created_at.time() if tx_to_update.created_at else time(0,0,0)
            combined_datetime = datetime.combine(new_date.date(), original_time)

            update_payload['created_at'] = combined_datetime


        updated_tx = self.repo.update_transaction(tx_to_update, update_payload)
        return updated_tx


    def get_transaction(self, tx_id, user_id):
        transaction = self.repo.get_by_id_and_user(user_id, tx_id)

        if not transaction:
            raise PermissionError(f"Transaction {tx_id} not found or access denied.")

        return transaction