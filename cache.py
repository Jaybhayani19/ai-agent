# cache.py
import os
import redis
import functools
import json
from tenacity import retry, stop_after_attempt, wait_exponential

# No longer need to call load_dotenv() here.
# The script will use the environment variables set by Docker.

try:
    redis_client = redis.from_url(os.getenv("REDIS_URL"))
    redis_client.ping()
    print("Successfully connected to Redis.")
except (redis.exceptions.ConnectionError, ValueError) as e:
    print(f"Could not connect to Redis: {e}. Caching will be disabled.")
    redis_client = None

def cache_result(ttl_seconds=3600):
    """
    A decorator to cache the results of a function in Redis.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not redis_client:
                return func(*args, **kwargs)

            # Assumes decorator is used on a class method, skips 'self'
            key_parts = [func.__name__] + list(args[1:]) + sorted(kwargs.items())
            cache_key = json.dumps(key_parts)

            cached_value = redis_client.get(cache_key)
            if cached_value:
                print(f"CACHE HIT for key: {cache_key}")
                return json.loads(cached_value)

            print(f"CACHE MISS for key: {cache_key}")
            result = func(*args, **kwargs)
            redis_client.setex(cache_key, ttl_seconds, json.dumps(result))

            return result
        return wrapper
    return decorator

def retry_on_failure(func):
    """
    A decorator to automatically retry a function on failure.
    """
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper
