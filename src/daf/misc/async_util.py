"""
Utilities related to the :mod:`asyncio` module.
"""
from typing import Union, Optional, Callable, Coroutine
from inspect import signature
from functools import wraps
from asyncio import Semaphore
from copy import copy
from contextlib import suppress
from datetime import datetime, timedelta

from .attributes import get_all_slots

import asyncio


__all__ = (
    "with_semaphore",
    "update_obj_param",
    "call_at",
    "except_return",
)


def with_semaphore(semaphore: Union[str, Semaphore], amount: Optional[int] = 1) -> Callable:
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


async def update_obj_param(
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
    parameters = signature(obj.__init__).parameters
    init_keys = parameters.keys()

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
            if k in kwargs:
                updated_params[k] = kwargs[k]
            else:
                updated_params[k] = getattr(obj, k)

        # Call the implementation __init__ function and
        # then initialize API related things
        obj.__init__(**updated_params)

        # Call additional initialization function (if it has one)
        if hasattr(obj, "initialize"):
            if isinstance(res := await obj.initialize(**init_options), Exception):
                raise res

    except Exception:
        # In case of failure, restore to original attributes
        for k in get_all_slots(type(obj)):
            with suppress(Exception):
                setattr(obj, k, getattr(current_state, k))

        raise


def call_at(fnc: Callable, when: Union[datetime, timedelta], *args, **kwargs) -> asyncio.Task:
    """
    Calls ``fnc`` at specific datetime with args and kwargs.
    """
    async def waiter():
        delay = when if isinstance(when, timedelta) else max((when.astimezone() - datetime.now().astimezone()), timedelta(0))
        delay = delay.total_seconds()
        while delay > 0:
            to_sleep = min(delay, 600)  # Maximum sleep of one day for precision purposes
            await asyncio.sleep(to_sleep)
            delay -= to_sleep

        if isinstance((r := fnc(*args, **kwargs)), Coroutine):
            await r

    return asyncio.create_task(waiter(), name=f'{fnc}_{args}_{kwargs}')


def except_return(fnc):
    """
    Wraps the ``fnc`` into a wrapper that returns False.
    If no exception is raised it returns the result of the ``fnc`` call.
    """
    @wraps(fnc)
    async def wrapper(*args, **kwargs):
        try:
            return await fnc(*args, **kwargs)
        except Exception as exc:
            return exc

    return wrapper
