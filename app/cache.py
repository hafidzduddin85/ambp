# app/cache.py
from functools import wraps
from time import time
from typing import Callable, Any, Optional, Tuple, Dict

_cache_store: Dict[str, Tuple[Any, float]] = {}
_default_ttl = 300  # default 5 menit

def cached(ttl: Optional[int] = None) -> Callable:
    """Decorator to cache a function's result for a given amount of time."""
    ttl = ttl or _default_ttl

    def decorator(fn: Callable):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            now = time()
            key = f"{fn.__module__}:{fn.__name__}:{args}:{kwargs}"
            entry = _cache_store.get(key)

            if entry is not None:
                data, timestamp = entry
                if now - timestamp < ttl:
                    return data

            try:
                data = fn(*args, **kwargs)
            except Exception as e:
                # Log the exception or handle it as needed
                print(f"Error caching {key}: {e}")
                raise

            _cache_store[key] = (data, now)
            return data

        return wrapper

    return decorator


def clear_cache(key: str) -> None:
    """Clear the cache for a given key."""
    if key in _cache_store:
        del _cache_store[key]

_cache = {}

def get_cached_data(key, builder, timeout=300):
    now = time()
    if key in _cache:
        value, ts = _cache[key]
        if now - ts < timeout:
            return value
    value = builder()
    _cache[key] = (value, now)
    return value

def clear_cache(key=None):
    if key:
        _cache.pop(key, None)
    else:
        _cache.clear()

