from datetime import  datetime, timedelta

from backend.finmate.transactions.repository import TransactionRepository
from backend.finmate.exceptions import BusinessLogicError

class DashboardService:

    def __init__(self):
        self.tx_repo = TransactionRepository()
        self.VALID_PERIODS = ['all', 'week', 'month']


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
    def _calculate_percentage_change(current, previous):
        current = float(current)
        previous = float(previous)
        if previous == 0:
            if current == 0:
                return 0.0
            return 100.0

        change = ((current - previous) / previous) * 100
        return round(change, 1)


    def get_dashboard_data(self, user_id, period):

        if period not in self.VALID_PERIODS:
            raise BusinessLogicError(f"Invalid period '{period}'. Must be one of: {', '.join(self.VALID_PERIODS)}.")

        start_date = self._calculate_start_date(period)

        today = datetime.now()
        first_day_current_month = today.replace(day=1)

        last_day_prev_month = first_day_current_month - timedelta(days=1)
        first_day_prev_month = last_day_prev_month.replace(day=1)

        # Previous Month Data
        prev_income = self.tx_repo.get_total_amount(user_id, "income", first_day_prev_month, last_day_prev_month)
        prev_expense = self.tx_repo.get_total_amount(user_id, "expense", first_day_prev_month, last_day_prev_month)

        # Current Period Data
        current_income = self.tx_repo.get_total_amount(user_id, "income", start_date, today)
        current_expense = self.tx_repo.get_total_amount(user_id, "expense", start_date, today)
        balance = self.tx_repo.get_current_balance(user_id)

        expenses_by_cat_raw = self.tx_repo.get_expense_by_category(user_id, start_date)
        balance_chart_raw = self.tx_repo.get_transactions_for_balance_chart(user_id, start_date)
        recent_transactions = self.tx_repo.get_recent_transactions(user_id, start_date)

        # Percentage Changes
        income_pct = self._calculate_percentage_change(current_income, prev_income)
        expense_pct = self._calculate_percentage_change(current_expense, prev_expense)

        if period == 'all':
            opening_balance = 0.0
        else:
            opening_balance=  self.tx_repo.get_opening_balance(user_id, start_date)

        category_labels = [item[0] if item[0] is not None else 'Uncategorized' for item in expenses_by_cat_raw]
        category_amounts = [float(item[1]) if item[1] is not None else 0.0 for item in expenses_by_cat_raw]

        current_balance_for_chart = float(opening_balance)
        daily_balances = {}

        for t in balance_chart_raw:
            amount_float = float(t.amount)
            if t.transaction_type == 'income':
                current_balance_for_chart += amount_float
            else:
                current_balance_for_chart -= amount_float
            date_str = t.created_at.strftime('%Y-%m-%d')

            daily_balances[date_str] = round(current_balance_for_chart, 2)

        balance_labels = list(daily_balances.keys())
        balance_data = list(daily_balances.values())

        return {
        "stats": {
            "current_income": float(current_income),
            "current_expense": float(current_expense),
            "current_balance": float(balance),
            "income_percentage_change": income_pct,
            "expense_percentage_change": expense_pct
        },
        "charts": {
            "expenses_by_category": {
                "labels": category_labels,
                "data": category_amounts
            },
            "balance_dynamics": {
                "labels": balance_labels,
                "data": balance_data
            }
        },
        "recent_transactions": [tx.to_dict() for tx in recent_transactions]
    }