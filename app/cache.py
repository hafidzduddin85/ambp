# app/cache.py
import time

_ref_cache = {}
_ref_expiry_seconds = 300  # 5 menit

def get_cached_data(key: str, loader_fn):
    now = time.time()
    if key in _ref_cache:
        data, timestamp = _ref_cache[key]
        if now - timestamp < _ref_expiry_seconds:
            return data

    data = loader_fn()
    _ref_cache[key] = (data, now)
    return data
