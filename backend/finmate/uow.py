from finmate.extensions import db


class UnitOfWork:

    def __init__(self):
        from finmate.transactions.repository import TransactionRepository
        from finmate.categories.repository import CategoryRepository
        from finmate.profile.repository import ProfileRepository
        from finmate.budgets.repository import BudgetRepository
        from finmate.auth.repository import AuthRepository

        self.transactions = TransactionRepository()
        self.categories = CategoryRepository()
        self.profile = ProfileRepository()
        self.budget = BudgetRepository()
        self.auth = AuthRepository()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.rollback()

    def commit(self):
        db.session.commit()

    def rollback(self):
        db.session.rollback()
