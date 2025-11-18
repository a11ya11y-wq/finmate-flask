from backend.finmate.transactions.repository import TransactionRepository

class DashboardService:

    def __init__(self):
        self.tx_repo = TransactionRepository()

    def get_dashboard_data(self, user_id, period):
        total_income = self.tx_repo.get_total_income(user_id, period)
        total_expense = self.tx_repo.get_total_expense(user_id, period)
        balance = self.tx_repo.get_current_balance(user_id)
        expenses_by_cat_raw = self.tx_repo.get_expense_by_category(user_id, period)
        balance_chart_raw = self.tx_repo.get_transactions_for_balance_chart(user_id, period)
        recent_transactions = self.tx_repo.get_recent_transactions(user_id, period)

        category_labels = [item[0] for item in expenses_by_cat_raw]
        category_amounts = [float(item[1]) for item in expenses_by_cat_raw]

        balance_labels = []
        balance_data = []
        current_balance_for_chart = 0.0

        for t in balance_chart_raw:
            amount_float = float(t.amount)
            if t.transaction_type == 'income':
                current_balance_for_chart += amount_float
            else:
                current_balance_for_chart -= amount_float
            balance_labels.append(t.created_at.strftime('%Y-%m-%d'))
            balance_data.append(round(current_balance_for_chart, 2))

        return {
        "stats": {
            "total_income": float(total_income),
            "total_expense": float(total_expense),
            "current_balance": float(balance)
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