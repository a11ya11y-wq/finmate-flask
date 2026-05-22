from core_service.extensions import db


class UnitOfWork:

    def __init__(self):
        from core_service.transactions.repository import TransactionRepository
        from core_service.categories.repository import CategoryRepository
        from core_service.profile.repository import ProfileRepository
        from core_service.budgets.repository import BudgetRepository
        from core_service.auth.repository import AuthRepository
        from core_service.reports.repository import ReportRepository

        self.transactions = TransactionRepository()
        self.categories = CategoryRepository()
        self.profile = ProfileRepository()
        self.budget = BudgetRepository()
        self.auth = AuthRepository()
        self.reports = ReportRepository()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.rollback()

    def commit(self):
        db.session.commit()

    def flush(self):
        db.session.flush()

    def rollback(self):
        db.session.rollback()
