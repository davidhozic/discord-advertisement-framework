"""
    This module contains definitions regarding miscellaneous
    items that can appear in multiple modules
"""
from collections.abc import Callable
from typing import Coroutine, Callable, Any, Dict, Optional, Union, Iterator
from collections.abc import Mapping
from asyncio import Semaphore
from functools import wraps, lru_cache
from inspect import getfullargspec
from copy import copy
from os import environ
from itertools import chain
from contextlib import suppress

from typeguard import typechecked

import weakref
import pickle


###############################
# Attributes
###############################
def _write_attr_once(obj: Any, name: str, value: Any):
    """
    Method that assigns an attribute only if it does not already exist.
    This is to prevent any ``.update()`` method calls from resetting critical
    variables that should not be changed,
    even if the objects goes thru initialization again.

    Parameters
    -------------
    obj: Any
        Object to safely write.

    name: str
        The name of the attribute to change.

    value: Any
        The value to change the attribute with.
    """
    # Write only if forced, or if not forced, then the attribute must not exist
    if not hasattr(obj, name):
        setattr(obj, name, value)


def get_all_slots(cls) -> list:
    """
    Returns slots of current class and it's bases. Skips the __weakref__ slot.
    Also returns internal_daf_id descriptor for tracked objects
    """
    ret = list(chain.from_iterable(getattr(class_, '__slots__', []) for class_ in cls.__mro__))

    with suppress(ValueError):
        ret.remove("__weakref__")

    return ret


###############################
# Update
###############################
async def _update(
    obj: object,
    *,
    init_options: dict = {},
    **kwargs
):
    """
    .. versionadded:: v2.0

    Used for changing the initialization parameters the obj
    was initialized with.

    .. warning::
        Upon updating, the internal state of objects get's reset,
        meaning you basically have a brand new created object.

    .. warning::
        This is not meant for manual use,
        but should be used only by the obj's method.

    Parameters
    -------------
    obj: object
        The object that contains a .update() method.
    init_options: dict
        Contains the initialization options used in
        .initialize() method for re-initializing certain objects.
        This is implementation specific and not necessarily available.
    Other:
        Other allowed parameters are the initialization parameters,
        first used on creation of the object.

    Raises
    ------------
    TypeError
        Invalid keyword argument was passed.
    Other
        Raised from .initialize() method.
    """
    # Retrieves list of call args
    init_keys = getfullargspec(obj.__init__.__wrapped__ if hasattr(obj.__init__, "__wrapped__") else obj.__init__).args
    init_keys.remove("self")
    # Make a copy of the current object for restoration in case failure
    current_state = copy(obj)
    try:
        for k in kwargs:
            if k not in init_keys:
                raise TypeError(
                    f"Argument `{k}` not allowed. (Allowed: {init_keys})"
                )
        # Most of the variables inside the object
        # have the same names as in the __init__ function.
        # This section stores attributes, that are the same,
        # into the `updated_params` dictionary and
        # then calls the __init__ method with the same parameters,
        # with the exception of start_period, end_period and start_now
        updated_params = {}
        for k in init_keys:
            updated_params[k] = kwargs[k] if k in kwargs else getattr(obj, k)

        # Call the implementation __init__ function and
        # then initialize API related things
        obj.__init__(**updated_params)

        # Call additional initialization function (if it has one)
        if hasattr(obj, "initialize"):
            await obj.initialize(**init_options)

    except Exception:
        # In case of failure, restore to original attributes
        for k in get_all_slots(type(obj)):
            with suppress(Exception):
                setattr(obj, k, getattr(current_state, k))

        raise


###########################
# Decorators
###########################
@typechecked
def _async_safe(semaphore: Union[str, Semaphore],
                amount: Optional[int] = 1) -> Callable:
    """
    Function that returns a safety decorator,
    which uses the :strong:`semaphore` parameter as a safety mechanism.

    This is for usage on :strong:`methods`

    Parameters
    ----------------
    semaphore: str
        Name of the semaphore attribute to take.
    amount: Optional[int]
        How many times to take the semaphore.

    Returns
    --------------
    Returns the safety decorator.

    Raises
    --------------
    TypeError
        The ``semaphore`` parameter is not a string describing
        the semaphore attribute of a table.
    """

    def __safe_access(coroutine: Union[Coroutine, Callable]) -> Coroutine:
        """
        Decorator that returns a method wrapper Coroutine that utilizes a
        asyncio semaphore to assure safe asynchronous operations.
        """
        async def sub_wrapper(sem: Semaphore, *args, **kwargs):
            for i in range(amount):
                await sem.acquire()

            result = None
            try:
                result = await coroutine(*args, **kwargs)
            finally:
                for i in range(amount):
                    sem.release()

            return result

        if isinstance(semaphore, str):
            # If string, assume that the string is the attribute name
            async def wrapper(self, *args, **kwargs):
                sem: Semaphore = getattr(self, semaphore)
                return await sub_wrapper(sem, self, *args, **kwargs)
        else:
            # Semaphore is directly passed.
            # Also works for normal (non-method) coroutines.
            async def wrapper(*args, **kwargs):
                return await sub_wrapper(semaphore, *args, **kwargs)

        return wraps(coroutine)(wrapper)

    return __safe_access


# Documentation
DOCUMENTATION_MODE = bool(environ.get("DOCUMENTATION", False))
if DOCUMENTATION_MODE:
    doc_titles: Dict[str, list] = {}


def doc_category(cat: str,
                 manual: Optional[bool] = False,
                 path: Optional[str] = None):
    """
    Used for marking under which category this should
    be put when auto generating documentation.

    Parameters
    ------------
    cat: str
        The name of the category to put this in.
    manual: Optional[bool]
        Should documentation be manually generated
    path: Optional[str]
        Custom path to the object.

    Returns
    ----------
    Decorator
        Returns decorator which marks the object
        to the category.
    """
    def _category(item):
        if DOCUMENTATION_MODE:
            doc_titles[cat].append((item, manual, path))
        return item

    if DOCUMENTATION_MODE:
        if cat not in doc_titles:
            doc_titles[cat] = []

    return _category


#######################################
# ID of different objects ID
#######################################
OBJECT_ID_MAP = weakref.WeakValueDictionary()


def get_by_id(id_: int):
    """
    Returns an object from it's id().
    """
    return OBJECT_ID_MAP.get(id_)


def get_object_id(obj: object) -> int:
    "Returns either internal daf's ID if it exist otherwise just the regular id()"
    return getattr(obj, "_daf_id", id(obj))


class ObjectReference:
    """
    Descriptive class that describes a reference to an object
    instead of the object itself. Useful for reducing unneeded storage.
    """
    def __init__(self, ref: int) -> None:
        self.ref = ref


def track_id(cls):
    """
    Decorator which replaces the __new__ method with a function that keeps a weak reference.
    """
    @wraps(cls, updated=[])
    class TrackedClass(cls):
        if hasattr(cls, "__slots__"):  # Don't break classes without slots
            __slots__ = ("__weakref__", "_daf_id")

        async def initialize(self, *args, **kwargs):
            _r = await super().initialize(*args, **kwargs)
            # Update weakref dictionary
            value = id(self)
            self._daf_id = value
            OBJECT_ID_MAP[value] = self
            return _r

        def __getattr__(self, __key: str):
            "Method that gets called whenever an attribute is not found."
            if __key == "_daf_id":
                return -1

            raise AttributeError(__key)

    return TrackedClass


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
                key = pickle.dumps((*args, kwargs))  # json.dumps()
            except TypeError:
                return fnc(*args, **kwargs)

            if (result := cache_dict.get(key, ...)) is not ...:
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
