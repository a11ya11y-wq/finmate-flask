from datetime import date, timedelta

from backend.finmate import  db
from sqlalchemy import func
from backend.finmate.models import Category, Transactions



class TransactionRepository:


    def get_base_query(self, user_id, period):
        base_query = Transactions.query.filter_by(user_id=user_id)
        today = date.today()
        if period == 'week':
            week_ago = today - timedelta(days=7)
            base_query = base_query.filter(Transactions.created_at >= week_ago)
        elif period == 'month':
            month_ago = today - timedelta(days=30)
            base_query = base_query.filter(Transactions.created_at >= month_ago)
        return base_query


    def get_recent_transactions(self, user_id, period, limit = 15):
        query = self.get_base_query(user_id, period)
        return query.order_by(Transactions.created_at.desc()).limit(limit).all()


    def get_total_income(self, user_id, period):
        query = self.get_base_query(user_id, period)
        return query.filter(Transactions.transaction_type == 'income') \
                       .with_entities(func.sum(Transactions.amount)) \
                       .scalar() or 0.0


    def get_total_expense(self, user_id, period):
        query = self.get_base_query(user_id, period)
        return query.filter(Transactions.transaction_type == 'expense') \
                        .with_entities(func.sum(Transactions.amount)) \
                        .scalar() or 0.0


    def get_current_balance(self, user_id):
        base_query = Transactions.query.filter_by(user_id=user_id)
        total_income = base_query.filter(Transactions.transaction_type == 'income') \
                       .with_entities(func.sum(Transactions.amount)) \
                       .scalar() or 0.0
        total_expense = base_query.filter(Transactions.transaction_type == 'expense') \
                        .with_entities(func.sum(Transactions.amount)) \
                        .scalar() or 0.0

        return total_income - total_expense


    def get_expense_by_category(self, user_id, period):
        query = self.get_base_query(user_id, period)
        return query.filter(
        Transactions.transaction_type == 'expense'
    ).outerjoin(Category).group_by(Category.name).with_entities(
        Category.name,
        func.sum(Transactions.amount)
    ).order_by(func.sum(Transactions.amount).desc()).all()


    def get_transactions_for_balance_chart(self, user_id, period):
        query = self.get_base_query(user_id, period)
        return query.order_by(Transactions.created_at.asc()).all()


    def create_transaction(self, data):
        new_transaction = Transactions(
            title=data.get('title'),
            amount=data.get('amount'),
            transaction_type=data.get('transaction_type'),
            category_id=data.get('category_id'),
            created_at=data.get('created_at'),
            user_id=data.get('user_id'),
            note=data.get('note')
        )
        try:
            db.session.add(new_transaction)
            db.session.commit()
            return new_transaction
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Error while creating transaction in DB: {e}")


    def get_by_id(self, tx_id):
        return Transactions.query.get(tx_id)


    def delete_transaction(self, transaction_obj):
        try:
            db.session.delete(transaction_obj)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Error while deleting transaction in DB: {e}")


    def update_transaction(self, transaction_obj, data):
        try:
            transaction_obj.title = data.get('title', transaction_obj.title)
            transaction_obj.amount = data.get('amount', transaction_obj.amount)
            transaction_obj.transaction_type = data.get('transaction_type', transaction_obj.transaction_type)
            transaction_obj.category_id = data.get('category_id', transaction_obj.category_id)
            transaction_obj.created_at = data.get('created_at', transaction_obj.created_at)
            transaction_obj.note = data.get('note', transaction_obj.note)
            db.session.commit()
            return transaction_obj
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Error while updating transaction in DB: {e}")