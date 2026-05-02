import functools
import json
import logging

from core_service import extensions


logger = logging.getLogger(__name__)


def redis_cache(ttl=300, key_builder=None):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not key_builder:
                logger.error(f"Error in @redis_cache for {func.__name__} : key_builder function is required.")
                raise ValueError(
                    f"Error in @redis_cache for {func.__name__} : key_builder function is required."
                )

            if not extensions.redis_client:
                logger.warning(f"Redis client not initialized in @redis_cache for {func.__name__}. Bypassing cache.")
                return func(*args, **kwargs)

            try:
                cache_key = key_builder(*args, **kwargs)
            except Exception as e:
                logger.exception(f"Error building cache key in @redis_cache for {func.__name__}")
                return func(*args, **kwargs)

            try:
                cached_data = extensions.redis_client.get(cache_key)
                if cached_data:
                    logger.debug(f"🟢 [CACHE HIT]: {cache_key}")
                    return json.loads(cached_data)
            except Exception as e:
                logger.exception(f"Error retrieving cache in @redis_cache for key {cache_key}")

            result = func(*args, **kwargs)

            try:
                extensions.redis_client.setex(
                    name=cache_key,
                    time=ttl,
                    value=json.dumps(result, default=str)
                )
            except Exception as e:
                logger.exception(f"Error setting cache in @redis_cache for key {cache_key}")
            logger.debug(f"🔴 [CACHE MISS]: {cache_key}")
            return result
        return wrapper
    return decorator


def invalidate_cache(key_pattern):
    if not key_pattern:
        logger.error("Key pattern must be provided for cache invalidation.")
        raise ValueError("Key pattern must be provided for cache invalidation.")

    if not extensions.redis_client:
        logger.warning("Redis client not initialized. Cannot invalidate cache.")
        return 0

    deleted_count = 0
    try:
        keys_to_delete = [key for key in extensions.redis_client.scan_iter(match=key_pattern)]

        if keys_to_delete:
            extensions.redis_client.delete(*keys_to_delete)
            deleted_count = len(keys_to_delete)
            logger.debug(f'Invalidated {deleted_count} cache entries matching pattern: {key_pattern}')
        else:
            logger.info(f'No cache entries found for pattern: {key_pattern}')
    except Exception as e:
        logger.exception(f"Error invalidating cache for pattern {key_pattern}")
    return deleted_count