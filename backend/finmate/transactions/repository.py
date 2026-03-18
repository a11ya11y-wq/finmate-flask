from decimal import Decimal
from typing import Optional

from sqlalchemy import func, case

from finmate.extensions import db
from finmate.models import Category, Transactions


class TransactionRepository:

    def get_base_query(self, user_id: int, start_date=None):
        base_query = Transactions.query.filter_by(user_id=user_id)
        if start_date:
            base_query = base_query.filter(Transactions.created_at >= start_date)
        return base_query

    def get_by_id(self, tx_id: int) -> Optional[Transactions]:
        return Transactions.query.get(tx_id)

    def get_by_id_and_user(self, user_id: int, tx_id: int) -> Optional[Transactions]:
        return Transactions.query.filter_by(user_id=user_id, id=tx_id).first()

    def get_recent_transactions(self, user_id: int, period, limit: int = 15) -> list[Transactions]:
        query = self.get_base_query(user_id, period)
        return query.order_by(Transactions.created_at.desc()).limit(limit).all()

    def get_total_amount(self, user_id: int, transaction_type, start_date, end_date) -> float:
        result = db.session.query(func.sum(Transactions.amount)) \
            .filter(
            Transactions.user_id == user_id,
            Transactions.transaction_type == transaction_type,
            Transactions.created_at >= start_date,
            Transactions.created_at <= end_date
        ).scalar()

        return float(result) if result else 0.0

    def get_current_balance(self, user_id: int) -> Decimal:
        current_balance = db.session.query(
            func.sum(
                case(
                    (Transactions.transaction_type == 'income', Transactions.amount),
                    (Transactions.transaction_type == 'expense', -Transactions.amount),
                    else_=0
                )
            )
        ).filter(Transactions.user_id == user_id).scalar() or 0.0
        return Decimal(current_balance)

    def get_current_balance_mono(self, user_id: int) -> Decimal:
        current_balance = db.session.query(
            func.sum(
                case(
                    (Transactions.transaction_type == 'income', Transactions.amount),
                    (Transactions.transaction_type == 'expense', -Transactions.amount),
                    else_=0
                )
            )
        ).filter(
            Transactions.user_id == user_id,
            Transactions.mono_id.isnot(None)
        ).scalar()

        return Decimal(current_balance or 0)

    def get_expense_by_category(self, user_id: int, period) -> list[tuple[str, float]]:
        query = self.get_base_query(user_id, period)
        return query.filter(
            Transactions.transaction_type == 'expense'
        ).outerjoin(Category).group_by(Category.name).with_entities(
            Category.name,
            func.sum(Transactions.amount)
        ).order_by(func.sum(Transactions.amount).desc()).all()

    def get_transactions_for_balance_chart(self, user_id: int, start_date) -> list[Transactions]:
        query = self.get_base_query(user_id, start_date)
        return query.order_by(Transactions.created_at.asc()).all()

    def get_opening_balance(self, user_id: int, start_date, initial_balance: int = 0) -> Decimal:
        historical_diff = db.session.query(
            func.sum(
                case(
                    (Transactions.transaction_type == 'income', Transactions.amount),
                    (Transactions.transaction_type == 'expense', -Transactions.amount),
                    else_=0
                )
            )
        ).filter(
            Transactions.user_id == user_id,
            Transactions.created_at < start_date
        ).scalar() or 0.0

        return Decimal(initial_balance) + Decimal(historical_diff)

    def get_count_by_category(self, user_id: int, cat_id: int) -> int:
        return Transactions.query.filter_by(user_id=user_id, category_id=cat_id).count()

    def get_existing_mono_ids(self, user_id: int, mono_ids: set) -> set:
        stmt = db.select(Transactions.mono_id).filter(
            Transactions.user_id == user_id,
            Transactions.mono_id.in_(mono_ids)
        ).execution_options(populate_existing=True)

        result = db.session.execute(stmt).scalars().all()

        return {str(id) for id in result}

    def create_transaction(self, data: dict) -> Transactions:
        new_transaction = Transactions(
            title=data.get('title'),
            amount=data.get('amount'),
            transaction_type=data.get('transaction_type'),
            category_id=data.get('category_id'),
            created_at=data.get('created_at'),
            user_id=data.get('user_id'),
            note=data.get('note')
        )
        db.session.add(new_transaction)
        return new_transaction

    def delete_transaction(self, transaction_obj: Transactions) -> None:
        db.session.delete(transaction_obj)

    def update_transaction(self, transaction_obj: Transactions, data: dict) -> Transactions:
        transaction_obj.title = data.get('title', transaction_obj.title)
        transaction_obj.amount = data.get('amount', transaction_obj.amount)
        transaction_obj.transaction_type = data.get('transaction_type', transaction_obj.transaction_type)
        transaction_obj.category_id = data.get('category_id', transaction_obj.category_id)
        transaction_obj.created_at = data.get('created_at', transaction_obj.created_at)
        transaction_obj.note = data.get('note', transaction_obj.note)

        return transaction_obj

    def bulk_insert_transactions(self, transactions_to_add: list[Transactions]) -> int:
        db.session.add_all(transactions_to_add)
        return len(transactions_to_add)

    def refresh_session(self) -> None:
        db.session.expire_all()
