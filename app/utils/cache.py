# app/cache.py
from functools import wraps
from time import time
from typing import Callable, Any, Optional, Dict, Tuple
import hashlib
import pickle
import logging

_cache: Dict[str, Tuple[Any, float]] = {}
_default_ttl = 300
_max_cache_size = 1000

def _generate_key(fn: Callable, args: tuple, kwargs: dict) -> str:
    """Generate optimized cache key"""
    try:
        # Use pickle for consistent serialization
        key_data = (fn.__module__, fn.__name__, args, tuple(sorted(kwargs.items())))
        serialized = pickle.dumps(key_data)
        return hashlib.md5(serialized).hexdigest()
    except (TypeError, pickle.PicklingError):
        # Fallback for unpicklable objects
        return f"{fn.__module__}:{fn.__name__}:{hash(args)}:{hash(tuple(sorted(kwargs.items())))}"

def _cleanup_cache():
    """Remove expired entries and enforce size limit"""
    if len(_cache) <= _max_cache_size:
        return
    
    now = time()
    # Remove expired entries first
    expired_keys = [k for k, (_, ts) in _cache.items() if now - ts > _default_ttl * 2]
    for key in expired_keys:
        _cache.pop(key, None)
    
    # If still over limit, remove oldest entries
    if len(_cache) > _max_cache_size:
        sorted_items = sorted(_cache.items(), key=lambda x: x[1][1])
        for key, _ in sorted_items[:len(_cache) - _max_cache_size]:
            _cache.pop(key, None)

def cached(ttl: Optional[int] = None) -> Callable:
    """Decorator to cache function results"""
    cache_ttl = ttl or _default_ttl

    def decorator(fn: Callable):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            key = _generate_key(fn, args, kwargs)
            now = time()
            
            # Check cache
            if key in _cache:
                data, timestamp = _cache[key]
                if now - timestamp < cache_ttl:
                    return data
            
            # Execute function
            try:
                data = fn(*args, **kwargs)
                _cache[key] = (data, now)
                
                # Periodic cleanup
                if len(_cache) % 100 == 0:
                    _cleanup_cache()
                    
                return data
            except Exception as e:
                logging.warning(f"Cache error for {fn.__name__}: {e}")
                raise
        return wrapper
    return decorator

def get_cached_data(key: str, builder: Callable, timeout: int = 300) -> Any:
    """Get cached data or build it"""
    now = time()
    
    if key in _cache:
        value, timestamp = _cache[key]
        if now - timestamp < timeout:
            return value
    
    value = builder()
    _cache[key] = (value, now)
    return value

def clear_cache(key: Optional[str] = None) -> None:
    """Clear cache entries"""
    if key:
        _cache.pop(key, None)
    else:
        _cache.clear()

def get_cache_stats() -> dict:
    """Get cache statistics"""
    now = time()
    expired = sum(1 for _, ts in _cache.values() if now - ts > _default_ttl)
    return {
        "total_entries": len(_cache),
        "expired_entries": expired,
        "active_entries": len(_cache) - expired,
        "max_size": _max_cache_size
    }

