import pytest

from core_service.dashboard.service import DashboardService
from core_service.exceptions import BusinessLogicError

@pytest.fixture
def profile_uow(patch_uow):
    mock_uow = patch_uow('core_service.dashboard.service.UnitOfWork')
    return mock_uow

class TestGetDashboardData:

    @pytest.parametrize("period", ["all", "week", "month"])
    def test_get_dashboard_data_valid_period(self, profile_uow):
        pass