import logging
from datetime import datetime, time

from core_service.exceptions import ResourceNotFound, BusinessLogicError
from core_service.models.transaction_model import Transactions
from core_service.uow import UnitOfWork
from core_service.utils.caching import invalidate_cache
from .schemas import TransactionCreateSchema, TransactionUpdateSchema

logger = logging.getLogger(__name__)


class TransactionService:

    def create_transaction(self, data: dict, user_id: int) -> Transactions:
        validated_data = TransactionCreateSchema.model_validate(data)
        category_id = validated_data.category_id

        with UnitOfWork() as uow:
            cat_obj = uow.categories.get_cat_by_id_and_user(category_id, user_id)

            if not cat_obj:
                logger.warning(f"Category {category_id} not found")
                raise ResourceNotFound(f"Category {category_id} not found or access denied.")

            payload = validated_data.model_dump()
            payload['user_id'] = user_id

            new_tx = uow.transactions.create_transaction(payload)
            uow.commit()

        try:
            self._clear_related_caches(user_id)
            logger.info(f"Transaction {new_tx.id} created for user {user_id}.")
        except Exception as e:
            logger.error(f"Post-commit action failed: {e}")
        return new_tx

    def delete_transaction(self, tx_id: int, user_id: int) -> bool:

        with UnitOfWork() as uow:
            tx_to_delete = uow.transactions.get_by_id_and_user(user_id, tx_id)

            if not tx_to_delete:
                logger.warning(f"Transaction {tx_id} not found for deletion.")
                raise ResourceNotFound(f"Transaction {tx_id} not found or access denied.")

            if tx_to_delete.mono_id:
                raise BusinessLogicError("You cannot delete a synchronized bank transaction.")

            uow.transactions.delete_transaction(tx_to_delete)
            uow.commit()

        try:
            self._clear_related_caches(user_id)
            logger.info(f"Transaction {tx_id} deleted for user {user_id}.")
        except Exception as e:
            logger.error(f"Post-commit action failed: {e}")
        return True

    def update_transaction(self, tx_id: int, user_id: int, data: dict) -> Transactions:

        validated_data = TransactionUpdateSchema.model_validate(data)
        update_payload = validated_data.model_dump(exclude_unset=True)
        if not update_payload:
            raise BusinessLogicError("No valid fields to update.")

        with UnitOfWork() as uow:

            tx_to_update = uow.transactions.get_by_id_and_user(user_id, tx_id)

            if not tx_to_update:
                logger.warning(f"Transaction {tx_id} not found for update.")
                raise ResourceNotFound(f"Transaction {tx_id} not found or access denied.")

            if tx_to_update.mono_id:
                forbidden_fields = ['amount', 'transaction_type', 'created_at']

                for field in forbidden_fields:
                    update_payload.pop(field, None)

                if not update_payload:
                    raise BusinessLogicError("You can only change the category and notes for a bank transaction.")

            if 'category_id' in update_payload:
                new_cat_id = update_payload['category_id']
                cat_obj = uow.categories.get_cat_by_id_and_user(new_cat_id, user_id)

                if not cat_obj:
                    logger.warning(f"Category {new_cat_id} not found for update.")
                    raise ResourceNotFound(f"Category {new_cat_id} not found or access denied.")

            if 'created_at' in update_payload:  # Додає час для дати (При редагуванні дати, час має залишатися той самий)
                new_date = update_payload['created_at']
                original_time = tx_to_update.created_at.time() if tx_to_update.created_at else time(0, 0, 0)
                combined_datetime = datetime.combine(new_date.date(), original_time)

                update_payload['created_at'] = combined_datetime

            updated_tx = uow.transactions.update_transaction(tx_to_update, update_payload)
            uow.commit()

        try:
            self._clear_related_caches(user_id)
            logger.info(f"Transaction {tx_id} updated for user {user_id}.")
        except Exception as e:
            logger.error(f"Post-commit action failed: {e}")
        return updated_tx

    def get_transaction(self, tx_id: int, user_id: int) -> Transactions:
        with UnitOfWork() as uow:
            transaction = uow.transactions.get_by_id_and_user(user_id, tx_id)

            if not transaction:
                logger.warning(f"Transaction {tx_id} not found.")
                raise ResourceNotFound(f"Transaction {tx_id} not found or access denied.")

        return transaction

    @staticmethod
    def _clear_related_caches(user_id):
        invalidate_cache(f"dashboard:{user_id}:*")
        invalidate_cache(f"categories:{user_id}")
        invalidate_cache(f"budgets:{user_id}")
