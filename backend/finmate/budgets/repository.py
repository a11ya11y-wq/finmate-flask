from sqlalchemy import func
from datetime import datetime, timezone

from backend.finmate import db
from backend.finmate.models import Budget, Transactions




class BudgetRepository:


    def get_all_budgets_by_user(self, user_id):
        return Budget.query.filter_by(user_id=user_id).all()


    def get_by_id(self, budget_id):
        return Budget.query.get(budget_id)


    def get_by_category_and_user(self, user_id, cat_id):
        return Budget.query.filter_by(user_id=user_id, category_id=cat_id).first()


    def get_count_by_user(self, user_id):
        return Budget.query.filter_by(user_id=user_id).count()


    def create_budget(self, data):
        new_budget = Budget(
            amount = data.get('amount'),
            category_id = data.get('category_id'),
            user_id = data.get('user_id'),
            created_at = data.get('created_at'),
            is_recurring = data.get('is_recurring')
        )
        try:
            db.session.add(new_budget)
            db.session.commit()
            return new_budget
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Error while creating budget in DB: {e}")


    def update_budget(self, budget_obj, data):
        try:
            budget_obj.amount = data.get('amount', budget_obj.amount)
            budget_obj.category_id = data.get('category_id', budget_obj.category_id)
            budget_obj.created_at = data.get('created_at', budget_obj.created_at)
            budget_obj.is_recurring = data.get('is_recurring', budget_obj.is_recurring)
            db.session.commit()
            return budget_obj
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Error while updating budget in DB: {e}")


    def delete_budget(self, budget_obj):
        try:
            db.session.delete(budget_obj)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise Exception(f'Error while deleting budget in DB: {e}')


    def get_recurring_spent_map(self, user_id):
        today = datetime.now(timezone.utc)
        start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        query = db.session.query(
            Budget.category_id,
            func.sum(Transactions.amount).label('total_spent')
        ).outerjoin(  # (LEFT JOIN)
            Transactions,
            (Budget.category_id == Transactions.category_id) &
            (Transactions.user_id == user_id) &
            (Transactions.transaction_type == 'expense') &
            # Дата транзакції >= ПОЧАТКУ МІСЯЦЯ
            (Transactions.created_at >= start_of_month)
        ).filter(
            # Знаходимо тільки ПЕРІОДИЧНІ бюджети
            Budget.user_id == user_id,
            Budget.is_recurring == True
        ).group_by(
            Budget.category_id
        ).all()

        spent_map = {
            item.category_id: float(item.total_spent or 0.0)
            for item in query
        }

        return spent_map # spent_map = {category_id: total_spent}



    def get_one_time_spent_map(self, user_id):
        one_time_expenses_query = db.session.query(
            Budget.category_id,
            func.sum(Transactions.amount).label('total_spent')
        ).outerjoin(  # (LEFT JOIN)
            Transactions,
            (Budget.category_id == Transactions.category_id) &
            (Transactions.created_at >= Budget.created_at) &
            (Transactions.user_id == user_id) &
            (Transactions.transaction_type == 'expense')
        ).filter(
            # Знаходимо тільки одноразові бюджети цього користувача
            Budget.user_id == user_id,
            Budget.is_recurring == False
        ).group_by(
            Budget.category_id
        ).all()
        # 'total_spent' може бути 'None', якщо витрат не було,
        # тому 'or 0.0'

        spent_map = {
            item.category_id: float(item.total_spent or 0.0)
            for item in one_time_expenses_query
        }

        return spent_map

