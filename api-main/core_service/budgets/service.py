import calendar
import logging
from datetime import datetime, timezone

from core_service.constants import MAX_BUDGET_PER_USER
from core_service.exceptions import ResourceNotFound, BusinessLogicError
from core_service.uow import UnitOfWork
from core_service.utils.caching import redis_cache, invalidate_cache
from .schemas import BudgetSchema

logger = logging.getLogger(__name__)


def budgets_key_builder(self, user_id):
    return f"budgets:{user_id}"


class BudgetService:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    @redis_cache(ttl=3600, key_builder=budgets_key_builder)
    def get_all_budgets_with_stats(self, user_id: int) -> list:
        all_budgets = self.uow.budget.get_all_budgets_by_user(user_id)
        recurring_spent_map = self.uow.budget.get_recurring_spent_map(user_id)
        one_time_spent_map = self.uow.budget.get_one_time_spent_map(user_id)

        today = datetime.now(timezone.utc)
        budgets_data = []

        for budget in all_budgets:
            total_spent = 0.0
            deadline_info = ""

            if budget.is_recurring:
                total_spent = recurring_spent_map.get(budget.category_id, 0.0)  # Верне 0 якщо немаэ трат

                days_in_month = calendar.monthrange(today.year, today.month)[1]
                days_left = days_in_month - today.day
                if days_left > 1:
                    deadline_info = f"{days_left} days left"
                elif days_left == 1:
                    deadline_info = "1 day left"
                else:
                    deadline_info = "Ends today"

            else:
                total_spent = one_time_spent_map.get(budget.category_id, 0.0)

                aware_created_at = budget.created_at.replace(tzinfo=timezone.utc)
                days_active = (today - aware_created_at).days
                if days_active > 1:
                    deadline_info = f"Active for {days_active} days"
                elif days_active == 1:
                    deadline_info = "Active for 1 day"
                else:
                    deadline_info = "Started today"

            percentage = 0
            if budget.amount > 0:
                percentage = (total_spent / float(budget.amount)) * 100
            remaining = float(budget.amount) - total_spent

            budget_dict = budget.to_dict()

            budget_dict.update({
                'total_spent': total_spent,
                'percentage': round(percentage, 2),
                'remaining': round(remaining, 2),
                'deadline_info': deadline_info
            })
            budgets_data.append(budget_dict)

        return sorted(
            budgets_data,
            key=lambda item: item['percentage'],
            reverse=True
        )

    def create_or_update_budget(self, user_id: int, data: dict):
        validated_data = BudgetSchema.model_validate(data)
        payload = validated_data.model_dump()
        category_id = payload['category_id']

        category = self.uow.categories.get_cat_by_id_and_user(category_id, user_id)
        if not category:
            raise ResourceNotFound(f"Category {category_id} not found or access denied.")

        budget_exist = self.uow.budget.get_by_category_and_user(user_id, category_id)

        if budget_exist:
            result = self.uow.budget.update_budget(budget_exist, payload)
            is_created = False
            logger.info(f"Budget updated for user {user_id} in category {category_id}")
        else:
            if self.uow.budget.get_count_by_user(user_id) >= MAX_BUDGET_PER_USER:
                raise BusinessLogicError(f'You have reached the limit of {MAX_BUDGET_PER_USER} budgets')

            payload['user_id'] = user_id
            result = self.uow.budget.create_budget(payload)
            is_created = True
            logger.info(f"New budget created for user {user_id} in category {category_id}")

        self.uow.flush()
        try:
            self._clear_related_caches(user_id)

        except Exception as e:
            logger.error(f"Post-commit action failed: {e}")
        return result, is_created

    def delete_budget(self, user_id, budget_id) -> bool:

        budget_to_delete = self.uow.budget.get_by_id_and_user(budget_id, user_id)
        if not budget_to_delete:
            logger.warning(f"Attempt to delete non-existing budget {budget_id} by user {user_id}")
            raise ResourceNotFound(f"Budget {budget_id} not found or access denied.")

        self.uow.budget.delete_budget(budget_to_delete)

        try:
            self._clear_related_caches(user_id)
            logger.info(f"Budget {budget_id} deleted for user {user_id}")
        except Exception as e:
            logger.error(f"Post-commit action failed: {e}")
        return True

    @staticmethod
    def _clear_related_caches(user_id):
        invalidate_cache(f"budgets:{user_id}")
