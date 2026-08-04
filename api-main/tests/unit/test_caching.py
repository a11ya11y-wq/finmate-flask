import json
import pytest
from unittest.mock import patch, MagicMock
from core_service.utils.caching import redis_cache, invalidate_cache
from core_service import extensions


def dummy_key_builder(user_id):
    return f"dummy:{user_id}"





class TestRedisCacheDecorator:

    def test_missing_key_builder(self):
        with pytest.raises(ValueError, match="key_builder function is required"):
            @redis_cache(ttl=60)
            def dummy_func(user_id):
                return {"status": "ok"}
                
            dummy_func(1)

    def test_redis_client_not_initialized(self, mocker):
        mocker.patch.object(extensions, "redis_client", None)

        @redis_cache(ttl=60, key_builder=dummy_key_builder)
        def dummy_func(user_id):
            return {"data": f"user_{user_id}"}

        result = dummy_func(1)
        assert result == {"data": "user_1"}

    def test_key_builder_exception_handled(self, mock_redis_client):
        def faulty_key_builder(user_id):
            raise Exception("Key generation failed")

        @redis_cache(ttl=60, key_builder=faulty_key_builder)
        def dummy_func(user_id):
            return {"data": "fallback"}

        result = dummy_func(1)
        assert result == {"data": "fallback"}
        mock_redis_client.get.assert_not_called()

    def test_cache_hit(self, mock_redis_client):
        mock_redis_client.get.return_value = json.dumps({"cached": "data"})

        @redis_cache(ttl=60, key_builder=dummy_key_builder)
        def dummy_func(user_id):
            return {"fresh": "data"}  # Should not be returned

        result = dummy_func(1)
        assert result == {"cached": "data"}
        mock_redis_client.get.assert_called_once_with("dummy:1")
        mock_redis_client.setex.assert_not_called()

    def test_cache_miss_and_set(self, mock_redis_client):
        mock_redis_client.get.return_value = None

        @redis_cache(ttl=60, key_builder=dummy_key_builder)
        def dummy_func(user_id):
            return {"fresh": "data"}

        result = dummy_func(1)
        assert result == {"fresh": "data"}
        mock_redis_client.get.assert_called_once_with("dummy:1")
        mock_redis_client.setex.assert_called_once_with(
            name="dummy:1",
            time=60,
            value=json.dumps({"fresh": "data"})
        )

    def test_redis_get_exception_handled(self, mock_redis_client):
        mock_redis_client.get.side_effect = Exception("Redis connection lost")

        @redis_cache(ttl=60, key_builder=dummy_key_builder)
        def dummy_func(user_id):
            return {"fresh": "data"}

        result = dummy_func(1)
        assert result == {"fresh": "data"}  # Gracefully falls back to calling function
        mock_redis_client.setex.assert_called_once() # Should still try to set cache

    def test_redis_setex_exception_handled(self, mock_redis_client):
        mock_redis_client.get.return_value = None
        mock_redis_client.setex.side_effect = Exception("Redis connection lost during set")

        @redis_cache(ttl=60, key_builder=dummy_key_builder)
        def dummy_func(user_id):
            return {"fresh": "data"}

        result = dummy_func(1)
        assert result == {"fresh": "data"}  # Returns result even if setting cache fails


class TestInvalidateCache:

    def test_missing_key_pattern(self):
        with pytest.raises(ValueError, match="Key pattern must be provided"):
            invalidate_cache("")

    def test_redis_client_not_initialized(self, mocker):
        mocker.patch.object(extensions, "redis_client", None)
        deleted_count = invalidate_cache("dummy:*")
        assert deleted_count == 0

    def test_keys_deleted_successfully(self, mock_redis_client):
        mock_redis_client.scan_iter.return_value = iter(["dummy:1", "dummy:2"])
        
        deleted_count = invalidate_cache("dummy:*")
        
        assert deleted_count == 2
        mock_redis_client.scan_iter.assert_called_once_with(match="dummy:*")
        mock_redis_client.delete.assert_called_once_with("dummy:1", "dummy:2")

    def test_no_keys_found(self, mock_redis_client):
        mock_redis_client.scan_iter.return_value = iter([])
        
        deleted_count = invalidate_cache("dummy:*")
        
        assert deleted_count == 0
        mock_redis_client.scan_iter.assert_called_once_with(match="dummy:*")
        mock_redis_client.delete.assert_not_called()

    def test_redis_exception_handled_gracefully(self, mock_redis_client):
        mock_redis_client.scan_iter.side_effect = Exception("Redis scan failed")
        
        deleted_count = invalidate_cache("dummy:*")
        
        assert deleted_count == 0
        mock_redis_client.delete.assert_not_called()
