import logging
import math
from datetime import datetime, timedelta
from decimal import Decimal

from core_service.constants import VALID_PERIODS
from core_service.exceptions import BusinessLogicError
from core_service.models.transaction_model import Transactions
from core_service.models.user_model import Users
from core_service.uow import UnitOfWork
from core_service.utils.caching import redis_cache

logger = logging.getLogger(__name__)


def dashboard_key_builder(self, user_id, period):
    return f"dashboard:{user_id}:{period}"


class DashboardService:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    @redis_cache(ttl=3600, key_builder=dashboard_key_builder)
    def get_dashboard_data(self, user_id: int, period) -> dict:

        if period not in VALID_PERIODS:
            logger.warning(f"Dashboard data retrieval failed: invalid period '{period}' for user {user_id}")
            raise BusinessLogicError(f"Invalid period '{period}'. Must be one of: {', '.join(VALID_PERIODS)}.")

        start_date = self._calculate_start_date(period)

        user = self.uow.profile.get_user_info(user_id)

        stats = self._get_stats(user, period, start_date)
        category_chart = self._get_category_chart(user, start_date)
        balance_dynamics = self._get_balance_dynamics(user, period, start_date)
        recent_tx = self._get_recent_tx(user, start_date)
        total_page = self._get_total_count_of_page(user, start_date)

        return {
            "stats": stats,
            "charts": {
                "expenses_by_category": category_chart,
                "balance_dynamics": balance_dynamics
            },
            "recent_transactions": {
                "data": recent_tx,
                "total_page": total_page
            }
        }

    def get_tx_history(self, user_id: int, period, page: int):
        start_date = self._calculate_start_date(period)
        offset = (page - 1) * 15
        recent_transactions = self.uow.transactions.get_recent_transactions(user_id, start_date, limit=15, offset=offset)
        transactions = [tx.to_dict() for tx in recent_transactions]
        return {
            "data": transactions
        }

    def _get_stats(self, user: Users, period, start_date) -> dict:
        today = datetime.now()
        user_id = user.id

        # Expense/Income Cards
        current_income = self.uow.transactions.get_total_amount(user_id, "income", start_date, today)
        current_expense = self.uow.transactions.get_total_amount(user_id, "expense", start_date, today)

        # Percentage Changes
        prev_start_date = self._calculate_prev_start_date(period, start_date)
        prev_end_date = start_date

        if prev_start_date:
            prev_income = self.uow.transactions.get_total_amount(user_id, "income", prev_start_date, prev_end_date)
            prev_expense = self.uow.transactions.get_total_amount(user_id, "expense", prev_start_date, prev_end_date)
        else:
            prev_income = 0.0
            prev_expense = 0.0

        income_pct = self._calculate_percentage_change(current_income, prev_income)
        expense_pct = self._calculate_percentage_change(current_expense, prev_expense)

        # Balance Card
        initial_balance = Decimal(user.initial_balance or 0)
        current_db_sum = Decimal(self.uow.transactions.get_current_balance(user_id) or 0)
        balance = initial_balance + current_db_sum

        return {
            "current_income": float(current_income),
            "current_expense": float(current_expense),
            "current_balance": float(balance),
            "income_percentage_change": income_pct,
            "expense_percentage_change": expense_pct
        }

    def _get_category_chart(self, user: Users, start_date) -> dict:
        expenses_by_cat_raw = self.uow.transactions.get_expense_by_category(user.id, start_date)
        category_labels = []
        category_amounts = []

        for name, amount in expenses_by_cat_raw:
            category_labels.append(name or "Uncategorized")
            category_amounts.append(float(amount or 0.0))

        return {
            "labels": category_labels,
            "data": category_amounts
        }

    def _get_balance_dynamics(self, user: Users, period, start_date) -> dict:
        balance_chart_raw = self.uow.transactions.get_transactions_for_balance_chart(user.id, start_date)

        # Calculate start point for the graph
        if period == 'all':
            opening_balance = user.initial_balance
        else:
            opening_balance = self.uow.transactions.get_opening_balance(user.id, start_date, user.initial_balance)

        current_balance = float(opening_balance or 0.0)

        labels = []
        data = []

        for t in balance_chart_raw:
            amount_float = float(t.amount)
            if t.transaction_type == 'income':
                current_balance += amount_float
            else:
                current_balance -= amount_float

            labels.append(t.created_at.strftime('%Y-%m-%d %H:%M:%S'))
            data.append(round(current_balance, 2))
            
        return {
            "labels": labels,
            "data": data
        }

    def _get_recent_tx(self, user: Users, start_date) -> list[Transactions]:
        recent_transactions = self.uow.transactions.get_recent_transactions(user.id, start_date)
        return [tx.to_dict() for tx in recent_transactions]

    def _get_total_count_of_page(self, user: Users, start_date) -> int:
        total_count = self.uow.transactions.get_total_count_of_tx(user.id, start_date)
        total_page = math.ceil(total_count / 15)
        return total_page

    @staticmethod
    def _calculate_start_date(period):
        now = datetime.now()
        today_midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
        if period == 'week':
            start_date = today_midnight - timedelta(weeks=1)
        elif period == 'month':
            start_date = today_midnight - timedelta(days=30)
        else:
            start_date = datetime.min
        return start_date

    @staticmethod
    def _calculate_prev_start_date(period, start_date):
        prev_start_date = None
        if period == "week":
            prev_start_date = start_date - timedelta(days=7)
        elif period == "month":
            prev_start_date = start_date - timedelta(days=30)
        return prev_start_date

    @staticmethod
    def _calculate_percentage_change(current, previous):
        current = float(current)
        previous = float(previous)
        if previous == 0:
            if current == 0:
                return 0.0
            return 100.0

        change = ((current - previous) / previous) * 100
        return round(change, 1)
