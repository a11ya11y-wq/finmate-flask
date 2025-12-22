from datetime import datetime, timezone
import calendar

from backend.finmate.budgets.repository import BudgetRepository
from backend.finmate.categories.repository import CategoryRepository
from .schemas import BudgetSchema
from backend.finmate.exceptions import ResourceNotFound, BusinessLogicError
from backend.finmate.utils.caching import redis_cache, invalidate_cache


def budgets_key_builder(self, user_id):
    return f"budgets:{user_id}"


class BudgetService:

    def __init__(self):
        self.repo = BudgetRepository()
        self.cat_repo = CategoryRepository()
        self.MAX_BUDGET_PER_USER = 5  # TODO: Замінити на імпорт з config


    @redis_cache(ttl=3600, key_builder=budgets_key_builder)
    def get_all_budgets_with_stats(self, user_id):
        all_budgets = self.repo.get_all_budgets_by_user(user_id)
        recurring_spent_map = self.repo.get_recurring_spent_map(user_id)
        one_time_spent_map = self.repo.get_one_time_spent_map(user_id)

        today = datetime.now(timezone.utc)
        budgets_data = []

        for budget in all_budgets:
            total_spent = 0.0
            deadline_info = ""

            if budget.is_recurring:
                total_spent = recurring_spent_map.get(budget.category_id, 0.0)# Верне 0 якщо немаэ трат

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


    def create_or_update_budget(self, user_id, data):

        validated_data = BudgetSchema.model_validate(data)

        payload = validated_data.model_dump()

        category_id = payload['category_id']
        category = self.cat_repo.get_by_id_and_user(category_id, user_id)
        if not category:
            raise ResourceNotFound(f"Category {category_id} not found or access denied.")

        budget_exist = self.repo.get_by_category_and_user(user_id, payload['category_id'])

        if budget_exist:
            updated_budget = self.repo.update_budget(budget_exist, payload)

            self._clear_related_caches(user_id)
            return updated_budget

        else:
            current_user_budget_count = self.repo.get_count_by_user(user_id)
            if current_user_budget_count >= self.MAX_BUDGET_PER_USER:
                raise BusinessLogicError(f'You have reached the limit of {self.MAX_BUDGET_PER_USER} budgets')
            else:
                payload['user_id'] = user_id

                new_budget = self.repo.create_budget(payload)

                self._clear_related_caches(user_id)
                return new_budget


    def delete_budget(self, user_id, budget_id):
        budget_to_delete = self.repo.get_by_id_and_user(budget_id, user_id)

        if not budget_to_delete:
            raise ResourceNotFound(f"Budget {budget_id} not found or access denied.")

        self.repo.delete_budget(budget_to_delete)

        self._clear_related_caches(user_id)
        return True

    @staticmethod
    def _clear_related_caches(user_id):
        invalidate_cache(f"budgets:{user_id}")




