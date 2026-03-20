import logging
import math
from datetime import datetime, timedelta
from decimal import Decimal

from finmate.constants import VALID_PERIODS
from finmate.exceptions import BusinessLogicError
from finmate.models.transaction_model import Transactions
from finmate.models.user_model import Users
from finmate.uow import UnitOfWork
from finmate.utils.caching import redis_cache

logger = logging.getLogger(__name__)


def dashboard_key_builder(self, user_id, period):
    return f"dashboard:{user_id}:{period}"


class DashboardService:

    @redis_cache(ttl=3600, key_builder=dashboard_key_builder)
    def get_dashboard_data(self, user_id: int, period) -> dict:

        if period not in VALID_PERIODS:
            logger.warning(f"Dashboard data retrieval failed: invalid period '{period}' for user {user_id}")
            raise BusinessLogicError(f"Invalid period '{period}'. Must be one of: {', '.join(VALID_PERIODS)}.")

        start_date = self._calculate_start_date(period)

        with UnitOfWork() as uow:
            user = uow.profile.get_user_info(user_id)

            stats = self._get_stats(uow, user, period, start_date)
            category_chart = self._get_category_chart(uow, user, start_date)
            balance_dynamics = self._get_balance_dynamics(uow, user, period, start_date)
            recent_tx = self._get_recent_tx(uow, user, start_date)
            total_page = self._get_total_count_of_page(uow, user, start_date)

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
        with UnitOfWork() as uow:
            recent_transactions = uow.transactions.get_recent_transactions(user_id, start_date, limit=15, offset=offset)
            transactions = [tx.to_dict() for tx in recent_transactions]
        return {
            "data": transactions
        }

    def _get_stats(self, uow: UnitOfWork, user: Users, period, start_date) -> dict:
        today = datetime.now()
        user_id = user.id

        # Expense/Income Cards
        current_income = uow.transactions.get_total_amount(user_id, "income", start_date, today)
        current_expense = uow.transactions.get_total_amount(user_id, "expense", start_date, today)

        # Percentage Changes
        prev_start_date = self._calculate_prev_start_date(period, start_date)
        prev_end_date = start_date

        if prev_start_date:
            prev_income = uow.transactions.get_total_amount(user_id, "income", prev_start_date, prev_end_date)
            prev_expense = uow.transactions.get_total_amount(user_id, "expense", prev_start_date, prev_end_date)
        else:
            prev_income = 0.0
            prev_expense = 0.0

        income_pct = self._calculate_percentage_change(current_income, prev_income)
        expense_pct = self._calculate_percentage_change(current_expense, prev_expense)

        # Balance Card
        initial_balance = Decimal(user.initial_balance or 0)
        current_db_sum = Decimal(uow.transactions.get_current_balance(user_id) or 0)
        balance = initial_balance + current_db_sum

        return {
            "current_income": float(current_income),
            "current_expense": float(current_expense),
            "current_balance": float(balance),
            "income_percentage_change": income_pct,
            "expense_percentage_change": expense_pct
        }

    @staticmethod
    def _get_category_chart(uow: UnitOfWork, user: Users, start_date) -> dict:
        expenses_by_cat_raw = uow.transactions.get_expense_by_category(user.id, start_date)
        category_labels = []
        category_amounts = []

        for name, amount in expenses_by_cat_raw:
            category_labels.append(name or "Uncategorized")
            category_amounts.append(float(amount) or 0.0)

        return {
            "labels": category_labels,
            "data": category_amounts
        }

    def _get_balance_dynamics(self, uow: UnitOfWork, user: Users, period, start_date) -> dict:
        balance_chart_raw = uow.transactions.get_transactions_for_balance_chart(user.id, start_date)

        # Calculate start point for the graph
        if period == 'all':
            opening_balance = user.initial_balance
        else:
            opening_balance = uow.transactions.get_opening_balance(user.id, start_date, user.initial_balance)

        current_balance_for_chart = float(opening_balance or 0.0)

        daily_balances = {}  # date: balance
        for t in balance_chart_raw:
            amount_float = float(t.amount)
            if t.transaction_type == 'income':
                current_balance_for_chart += amount_float
            else:
                current_balance_for_chart -= amount_float

            date_str = t.created_at.strftime('%Y-%m-%d')  # Choose correct time format
            # Overwrites to keep the end-of-day balance.
            daily_balances[date_str] = round(current_balance_for_chart, 2)

        balance_labels = list(daily_balances.keys())
        balance_data = list(daily_balances.values())
        return {
            "labels": balance_labels,
            "data": balance_data
        }

    @staticmethod
    def _get_recent_tx(uow: UnitOfWork, user: Users, start_date) -> list[Transactions]:
        recent_transactions = uow.transactions.get_recent_transactions(user.id, start_date)
        return [tx.to_dict() for tx in recent_transactions]

    def _get_total_count_of_page(self, uow: UnitOfWork, user: Users, start_date) -> int:
        total_count = uow.transactions.get_total_count_of_tx(user.id, start_date)
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
