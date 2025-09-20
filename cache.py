# cache.py
import os
import redis
import functools
import json
from tenacity import retry, stop_after_attempt, wait_exponential

# This is a "singleton" pattern to hold our connection
_redis_client = None

def get_redis_client():
    """Creates and reuses a single Redis client connection."""
    global _redis_client
    if _redis_client is None:
        try:
            redis_url = os.getenv("REDIS_URL")
            if not redis_url:
                raise ValueError("REDIS_URL is not set")
            _redis_client = redis.from_url(redis_url)
            _redis_client.ping()
            print("Successfully connected to Redis.")
        except (redis.exceptions.ConnectionError, ValueError) as e:
            print(f"Could not connect to Redis: {e}. Caching will be disabled.")
            _redis_client = None # Ensure it stays None on failure
    return _redis_client

def cache_result(ttl_seconds=3600):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            redis_client = get_redis_client() # <-- Get connection here
            if not redis_client:
                return func(*args, **kwargs)

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
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper
