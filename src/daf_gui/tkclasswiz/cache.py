"""
Utility module used for caching.
"""
from typing import Callable
from functools import wraps
import pickle


__all__ = (
    "cache_result",
)


# Caching
def cache_result(max: int = 256):
    """
    Caching function that also allows dictionary and lists to be used as a key.

    Parameters
    --------------
    max: int
        The maximum number of items inside the cache.
    """
    def _decorator(fnc: Callable):
        cache_dict = {}

        @wraps(fnc)
        def wrapper(*args, **kwargs):
            try:
                # Convert to pickle string to allow hashing of non-hashables (dictionaries, lists, ...)
                key = pickle.dumps((*args, kwargs))
            except Exception:
                return fnc(*args, **kwargs)

            result = cache_dict.get(key, Ellipsis)
            if result is not Ellipsis:
                return result

            result = fnc(*args, **kwargs)
            cache_dict[key] = result

            if len(cache_dict) > max:
                items = list(cache_dict.items())[:max // 2]
                cache_dict.clear()
                cache_dict.update(items)

            return result

        return wrapper

    return _decorator
