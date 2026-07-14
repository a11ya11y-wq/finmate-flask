from unittest.mock import MagicMock

import allure
import pytest


@pytest.fixture(scope="function", autouse=True)
@allure.title("Mocking Redis Client and Cache Invalidation")
def mock_redis_client(mocker):
    # Mock redis deco
    with allure.step("Mocking Redis client for caching"):
        mock_redis = mocker.patch("core_service.extensions.redis_client")
        mock_redis.get.return_value = None

    # Mock cache invalidation
    with allure.step("Mocking cache invalidation for services"):
        mocker.patch("core_service.transactions.service.invalidate_cache")
        mocker.patch("core_service.profile.service.invalidate_cache")
        mocker.patch("core_service.monobank.service.invalidate_cache")
        mocker.patch("core_service.reports.service.invalidate_cache")
    return mock_redis
