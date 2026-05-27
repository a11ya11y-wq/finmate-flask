import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import requests

from core_service.exceptions import BusinessLogicError, ForbiddenError
from core_service.exceptions import ThrottlingError
from core_service.models.transaction_model import Transactions
from core_service.profile.service import ProfileService
from core_service.uow import UnitOfWork
from core_service.utils.caching import invalidate_cache
from .api_client import MonoAPI

logger = logging.getLogger(__name__)


class MonobankService:

    def __init__(self, uow: UnitOfWork):
        self.profile_service = ProfileService(uow)
        self.uow = uow

    def sync_tx(self, user_id: int) -> int:

        user = self.uow.profile.get_user_info(user_id)
        token_bytes = user.monobank_api_token

        if not user or not user.monobank_api_token:
            logger.warning(f"Monobank sync failed: API token not found or access denied for user {user_id}")
            raise BusinessLogicError("API token not found or user access denied.")

        api = MonoAPI(encrypted_token_bytes=token_bytes)

        client_info = self._get_client_info(api, user_id)
        account_id, real_card_balance = self._get_card_stats(client_info)
        self.uow.profile.update_real_balance(user, real_card_balance)

        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        from_time = int(thirty_days_ago.timestamp())
        transactions_from_mono = self._get_tx_from_mono(api, user_id, account_id, from_time)
        added_count = self._add_new_tx_from_mono(self.uow, user_id, transactions_from_mono)

        calculated_initial_balance = self.profile_service.recalculate_initial_point(user_id)
        self.uow.flush()

        logger.info(f"Balance adjusted. New Initial: {calculated_initial_balance}")
        return added_count

    @staticmethod
    def _get_client_info( api: MonoAPI, user_id: int) -> dict:
        try:
            client_info = api.get_client_info()
            if 'errorDescription' in client_info:
                raise ForbiddenError(client_info['errorDescription'])

        except requests.RequestException as e:
            logger.exception(f"Monobank API request error for user {user_id}")
            raise ThrottlingError(f"Monobank connection failed: {str(e)}")

        except Exception as e:
            logger.exception(f"Monobank sync failed for user {user_id}")
            raise ForbiddenError(f"Invalid token or API error: {str(e)}")

        return client_info

    @staticmethod
    def _get_card_stats(client_info: dict) -> tuple:
        accounts = client_info.get('accounts', [])
        if not accounts:
            raise BusinessLogicError("No accounts found in Monobank")

        account_id = None
        real_card_balance_cents = 0

        for acc in accounts: # Choose correct card
            if acc.get('type') == 'black' and acc.get('currencyCode') == 980:
                account_id = acc.get('id')
                real_card_balance_cents = acc.get('balance')
                break

        if not account_id: # If we can`t find correct card
            account_id = accounts[0]['id']
            real_card_balance_cents = accounts[0]['balance']
            logger.info(f"No correct card found in Monobank")

        real_card_balance = Decimal(real_card_balance_cents) / Decimal(100)
        logger.info(f"Selected Account ID for sync: {account_id}")
        return account_id, real_card_balance

    @staticmethod
    def _get_tx_from_mono(api: MonoAPI, user_id: int, account_id, from_time) -> dict:
        transactions_from_mono = api.get_transactions(account_id, from_time)

        if isinstance(transactions_from_mono, dict) and transactions_from_mono.get('errorDescription'):
            error_msg = transactions_from_mono['errorDescription']

            if error_msg == 'Too many requests':
                logger.warning(f"Monobank API throttling error for user {user_id}: {error_msg}")
                raise ThrottlingError(error_msg)

            logger.error(f"Monobank API error for user {user_id}: {error_msg}")
            raise ForbiddenError(f'Monobank API Error: {error_msg}')

        return  transactions_from_mono

    @staticmethod
    def _add_new_tx_from_mono(uow: UnitOfWork, user_id,  transactions_from_mono: dict) -> int:
        default_category = uow.categories.get_by_name_and_user("Uncategorized", user_id)

        if not default_category:
            data = {"name": "Uncategorized"}
            default_category = uow.categories.create_category(user_id, data)

        mcc_map = {}
        all_categories = uow.categories.get_all_categories(user_id)

        for cat in all_categories:
            mcc_code_val = cat.mcc_code
            if mcc_code_val:
                codes = mcc_code_val.split(',')
                for code in codes:
                    mcc_map[code.strip()] = cat.id

        mono_ids = {t['id'] for t in transactions_from_mono}
        existing_ids = uow.transactions.get_existing_mono_ids(user_id, mono_ids)

        new_transactions_to_add = []
        for t_dict in transactions_from_mono:
            if t_dict['id'] not in existing_ids:
                mcc_code_str = str(t_dict.get('mcc', ''))
                assigned_category_id = mcc_map.get(mcc_code_str, default_category.id)

                new_tx = Transactions(
                    title=t_dict.get('description', 'Monobank Transaction'),

                    amount=Decimal(abs(t_dict['amount'])) / Decimal(100),

                    created_at=datetime.fromtimestamp(t_dict['time'], tz=timezone.utc),
                    user_id=user_id,
                    mono_id=t_dict['id'],
                    transaction_type='income' if t_dict['amount'] > 0 else 'expense',
                    category_id=assigned_category_id
                )
                new_transactions_to_add.append(new_tx)

        added_count = 0
        if new_transactions_to_add:
            added_count = uow.transactions.bulk_insert_transactions(new_transactions_to_add)
            logger.info(f"Added {added_count} new transactions for user {user_id} from Monobank.")
        else:
            logger.info(f"No new transactions to add for user {user_id} from Monobank.")
        return added_count


    @staticmethod
    def _clear_related_caches(user_id: int):
        invalidate_cache(f"dashboard:{user_id}:*")
        invalidate_cache(f"budgets:{user_id}")
        invalidate_cache(f"profile:{user_id}")
