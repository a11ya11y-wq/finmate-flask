from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func

from core_service.extensions import db
from core_service.models import Budget, Transactions


class BudgetRepository:

    def get_all_budgets_by_user(self, user_id: int) -> list[Budget]:
        return Budget.query.filter_by(user_id=user_id).all()

    def get_by_id(self, budget_id: int) -> Optional[Budget]:
        return Budget.query.get(budget_id)

    def get_by_id_and_user(self, budget_id: int, user_id: int) -> Optional[Budget]:
        return Budget.query.filter_by(id=budget_id, user_id=user_id).first()

    def get_by_category_and_user(self, user_id: int, cat_id: int) -> Optional[Budget]:
        return Budget.query.filter_by(user_id=user_id, category_id=cat_id).first()

    def get_count_by_user(self, user_id: int) -> int:
        return Budget.query.filter_by(user_id=user_id).count()

    def create_budget(self, data: dict) -> Budget:
        new_budget = Budget(
            amount=data.get('amount'),
            category_id=data.get('category_id'),
            user_id=data.get('user_id'),
            created_at=data.get('created_at'),
            is_recurring=data.get('is_recurring')
        )
        db.session.add(new_budget)
        return new_budget

    def update_budget(self, budget_obj: Budget, data: dict) -> Budget:
        budget_obj.amount = data.get('amount', budget_obj.amount)
        budget_obj.category_id = data.get('category_id', budget_obj.category_id)
        budget_obj.created_at = data.get('created_at', budget_obj.created_at)
        budget_obj.is_recurring = data.get('is_recurring', budget_obj.is_recurring)
        return budget_obj

    def delete_budget(self, budget_obj: Budget) -> None:
        db.session.delete(budget_obj)

    def get_recurring_spent_map(self, user_id: int) -> dict:
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
        return spent_map  # spent_map = {category_id: total_spent}

    def get_one_time_spent_map(self, user_id: int) -> dict:
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
