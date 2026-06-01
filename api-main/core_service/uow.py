from core_service.extensions import db
import logging


logger = logging.getLogger(__name__)

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

        self._post_commit_hooks = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.rollback()
            self._post_commit_hooks.clear()
        else:
            self.commit()
            for hook in self._post_commit_hooks:
                try:
                    hook()
                except Exception as e:
                    hook_name = getattr(hook, '__name__', str(hook))
                    logger.exception(f"Post-commit hook '{hook_name}' failed!")
                    
            self._post_commit_hooks.clear()

    def on_commit(self, callback):
        self._post_commit_hooks.append(callback)

    def commit(self):
        db.session.commit()

    def flush(self):
        db.session.flush()

    def rollback(self):
        db.session.rollback()
