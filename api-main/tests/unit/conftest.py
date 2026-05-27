import pytest
from unittest.mock import MagicMock



@pytest.fixture(scope='function')
def mock_uow_context():
    mock_context = MagicMock()

    mock_context.transactions = MagicMock()
    mock_context.categories = MagicMock()
    mock_context.profile = MagicMock()
    mock_context.budget = MagicMock()
    mock_context.auth = MagicMock()
    mock_context.reports = MagicMock()

    return mock_context


@pytest.fixture(scope='function')
def patch_uow(mocker, mock_uow_context):

    def _patcher(import_path: str):
        mock_uow_class = mocker.patch(import_path, autospec=True)
        
        mock_uow_class.return_value.__enter__.return_value = mock_uow_context
        return mock_uow_context

    return _patcher


@pytest.fixture(scope='function', autouse=True)
def mock_redis_client(mocker):
    # Mock redis deco
    mock_redis = mocker.patch("core_service.extensions.redis_client")
    mock_redis.get.return_value = None

    # Mock cache invalidation 
    mocker.patch("core_service.transactions.service.invalidate_cache")
    mocker.patch("core_service.profile.service.invalidate_cache")
    mocker.patch("core_service.monobank.service.invalidate_cache")
    mocker.patch("core_service.reports.service.invalidate_cache")

    return mock_redis