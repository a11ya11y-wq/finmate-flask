import functools
import json

from backend.finmate import extensions

def redis_cache(ttl=300, key_builder=None):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not key_builder:
                raise ValueError(
                    f"Error in @redis_cache for {func.__name__} : key_builder function is required."
                )
            try:
                cache_key = key_builder(*args, **kwargs)
            except Exception as e:
                print("Error building cache key:", e)
                return func(*args, **kwargs)

            try:
                cached_data = extensions.redis_client.get(cache_key)
                if cached_data:
                    print(f"🟢 [CACHE HIT]: {cache_key}")
                    return json.loads(cached_data)
            except Exception as e:
                print(f"Redis read error: {e}")

            result = func(*args, **kwargs)

            try:
                extensions.redis_client.setex(
                    name=cache_key,
                    time=ttl,
                    value=json.dumps(result, default=str)
                )
            except Exception as e:
                print(f"Error caching data: {e}")
            print(f"🔴 [CACHE MISS]: {cache_key}")
            return result
        return wrapper
    return decorator


def invalidate_cache(key_pattern):
    if not key_pattern:
        raise ValueError("Key pattern must be provided for cache invalidation.")
    deleted_count = 0
    try:
        keys_to_delete = [key for key in extensions.redis_client.scan_iter(match=key_pattern)]

        if keys_to_delete:
            extensions.redis_client.delete(*keys_to_delete)
            deleted_count = len(keys_to_delete)
            print(f'Invalidated {deleted_count} cache entries matching pattern: {key_pattern}')
        else:
            print(f'No cache entries found for pattern: {key_pattern}')
    except Exception as e:
        print(f"Error invalidating cache for pattern {key_pattern}: {e}")
    return deleted_count