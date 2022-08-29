"""
    This module contains definitions regarding miscellaneous
    items that can appear in multiple modules
"""
from typing import Coroutine, Callable, Any, Optional
from asyncio import Semaphore
from functools import wraps
from inspect import getfullargspec
from copy import copy

###############################
# Safe access functions
###############################
def _write_attr_once(obj: Any, name: str, value: Any):
    """
    Method that assigns an attribute only if it does not already have a reference to an object.
    This is to prevent any ``.update()`` method calls from resetting critical variables that should not be changed,
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
    if not hasattr(obj, name): # Write only if forced, or if not forced, then the attribute must not exist
        setattr(obj, name, value)


async def _update(obj: Any, *, init_options: dict = {}, **kwargs):
    """
    .. versionadded:: v2.0

    Used for changing the initialization parameters the obj was initialized with.

    .. warning::
        Upon updating, the internal state of objects get's reset, meaning you basically have a brand new created object.

    .. warning::
        This is not meant for manual use, but should be used only by the obj's method.

    Parameters
    -------------
    obj: Any
        The object that contains a .update() method.
    init_options: dict
        Contains the initialization options used in .initialize() method for re-initializing certain objects.
        This is implementation specific and not necessarily available.
    Other:
        Other allowed parameters are the initialization parameters first used on creation of the object.

    Raises
    ------------
    TypeError
        Invalid keyword argument was passed.
    Other
        Raised from .initialize() method.
    """
    init_keys = getfullargspec(obj.__init__.__wrapped__ if hasattr(obj.__init__, "__wrapped__") else obj.__init__).args # Retrieves list of call args
    init_keys.remove("self")
    current_state = copy(obj) # Make a copy of the current object for restoration in case of update failure
    try:
        for k in kwargs:
            if k not in init_keys:
                raise TypeError(f"Keyword argument `{k}` was passed which is not allowed. The update method only accepts the following keyword arguments: {init_keys}")
        # Most of the variables inside the object have the same names as in the __init__ function.
        # This section stores attributes, that are the same, into the `updated_params` dictionary and
        # then calls the __init__ method with the same parameters, with the exception of start_period, end_period and start_now parameters
        updated_params = {}
        for k in init_keys:
            # Store the attributes that match the __init__ parameters into `updated_params`
            updated_params[k] = kwargs[k] if k in kwargs else getattr(obj, k)

        # Call the implementation __init__ function and then initialize API related things
        obj.__init__(**updated_params)
        # Call additional initialization function (if it has one)
        if hasattr(obj, "initialize"):
            await obj.initialize(**init_options)

    except Exception:
        # In case of failure, restore to original attributes
        for k in type(obj).__slots__:
            setattr(obj, k, getattr(current_state, k))

        raise


###########################
# Decorators
###########################
def _async_safe(semaphore: str, amount: Optional[int]=1) -> Callable:
    """
    Function that returns a safety decorator, which uses the :strong:`semaphore` parameter
    as a safety mechanism.

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
        The ``semaphore`` parameter is not a string describing the semaphore attribute of a table.
    """

    def __safe_access(coroutine: Coroutine) -> Coroutine:
        """
        Decorator that returns a method wrapper Coroutine that utilizes a
        asyncio semaphore to assure safe asynchronous operations.
        """
        @wraps(coroutine)
        async def wrapper(self, *args, **kwargs):
            sem: Semaphore = getattr(self, semaphore)
            for i in range(amount):
                await sem.acquire()

            result = await coroutine(self, *args, **kwargs)

            for i in range(amount):
                sem.release()

            return result

        return wrapper


    if not isinstance(semaphore, str):
        raise TypeError("semaphore parameter must be an attribute name of the asyncio semaphore inside the object")

    return __safe_access
