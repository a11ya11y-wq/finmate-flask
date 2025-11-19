import requests
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from backend.finmate.profile.repository import ProfileRepository
from backend.finmate.transactions.repository import TransactionRepository
from backend.finmate.categories.repository import CategoryRepository
from backend.finmate.categories.service import CategoryService
from .api_client import MonoAPI
from backend.finmate.exceptions import ThrottlingError
from backend.finmate.models.transaction_model import Transactions



class MonobankService:
    def __init__(self):
        self.profile_repo = ProfileRepository()
        self.cat_repo = CategoryRepository()
        self.tx_repo = TransactionRepository()
        self.cat_service = CategoryService()


    def sync_tx(self, user_id):
        user = self.profile_repo.get_user_info(user_id)
        token_bytes = user.monobank_api_token

        if not user or not token_bytes:
            raise PermissionError("API token not found or user access denied.")

        api = MonoAPI(encrypted_token_bytes=token_bytes)

        try:
            client_info = api.get_client_info()

            if isinstance(client_info, dict) and client_info.get('errorDescription'):
                error_msg = client_info['errorDescription']
                raise requests.exceptions.RequestException(error_msg)

        except Exception as e:
            raise PermissionError(f'Monobank or token error: {e}. Please update your token.')

        account_id = client_info['accounts'][0]['id']

        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        from_time = int(thirty_days_ago.timestamp())

        transactions_from_mono = api.get_transactions(account_id, from_time)

        if isinstance(transactions_from_mono, dict) and transactions_from_mono.get('errorDescription'):
            error_msg = transactions_from_mono['errorDescription']

            if error_msg == 'Too many requests':
                raise ThrottlingError(error_msg)

            raise PermissionError(f'Monobank API Error: {error_msg}')

        default_category = self.cat_repo.get_by_name_and_user("Uncategorized", user_id)

        if not default_category:
            data = {"name": "Uncategorized"}
            self.cat_service.create_category(user_id, data)

        mcc_map = {}
        all_categories = self.cat_service.get_all_categories(user_id)

        for cat in all_categories:
            if cat.mcc_code:
                codes = cat.mcc_code.split(',')
                for code in codes:
                    mcc_map[code.strip()] = cat.id

        mono_ids = {t['id'] for t in transactions_from_mono}

        existing_ids = self.tx_repo.get_existing_mono_ids(user_id, mono_ids) #{str(id_tuple[0] for id_tuple in existing_ids_query)}
        new_transactions_to_add = []

        for t_dict in transactions_from_mono:
            if t_dict['id'] not in existing_ids:
                mcc_code_str = str(t_dict.get('mcc', ''))
                assigned_category_id = mcc_map.get(mcc_code_str, default_category.id)

                new_tx = Transactions(
                    title=t_dict['description'],

                    amount=Decimal(abs(t_dict['amount']) / 100),

                    created_at=datetime.fromtimestamp(t_dict['time'], tz=timezone.utc),
                    user_id=user_id,
                    mono_id=t_dict['id'],
                    transaction_type='income' if t_dict['amount'] > 0 else 'expense',
                    category_id=assigned_category_id
                )
                new_transactions_to_add.append(new_tx)

        if not new_transactions_to_add:
            return 0

        added_count = self.tx_repo.bulk_insert_transactions(new_transactions_to_add)

        return added_count
