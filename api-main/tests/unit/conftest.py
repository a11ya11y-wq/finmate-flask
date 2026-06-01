import pytest
from unittest.mock import MagicMock


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