# app/cache.py
import time
from typing import Callable, Any

_cache_store = {}
_default_ttl = 300  # default 5 menit

def get_cached_data(key: str, loader_fn: Callable[[], Any], ttl: int = _default_ttl) -> Any:
    now = time.time()
    entry = _cache_store.get(key)

    if entry:
        data, timestamp = entry
        if now - timestamp < ttl:
            return data

    data = loader_fn()
    _cache_store[key] = (data, now)
    return data

def clear_cache(key: str):
    _cache_store.pop(key, None)
