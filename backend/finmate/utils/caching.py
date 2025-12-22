import functools
import json

from backend.finmate.extensions import redis_client

def redis_cache(ttl=300, key_builder=None):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not key_builder:
                raise ValueError(
                    f"Error in @redis_cache for {func.__name__}"
                )
            try:
                cache_key = key_builder(*args, **kwargs)
            except Exception as e:
                print("Error building cache key:", e)
                return func(*args, **kwargs)

            try:
                cached_data = redis_client.get(cache_key)
                if cached_data:
                    return json.loads(cached_data)
            except Exception as e:
                print(f"Redis read error: {e}")

            result = func(*args, **kwargs)

            try:
                redis_client.setex(
                    name=cache_key,
                    time=ttl,
                    value=json.dumps(result, default=str)
                )
            except Exception as e:
                print(f"Error caching data: {e}")

            return result
        return wrapper
    return decorator