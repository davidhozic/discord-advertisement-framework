"""
    This module contains definitions regarding miscellaneous
    items that can appear in multiple modules
"""
from typing import Coroutine, Callable, Any, Optional, Union, TypeVar
from asyncio import Semaphore
from .exceptions import DAF_INVALID_TYPE, DAFParameterError
from functools import wraps
from typeguard import typechecked
from inspect import isclass

###############################
# Type vars
T = TypeVar("T")
###############################

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

        wrapper.__annotations__ = coroutine.__annotations__ # Keep the same type hints

        return wrapper


    if not isinstance(semaphore, str):
        raise TypeError("semaphore parameter must be an attribute name of the asyncio semaphore inside the object")

    return __safe_access



def _enforce_annotations(func: Union[Callable, T]) -> T:
    """
    Decorator that wraps method fnc in a function that
    raises DAFParameterError(code=DAF_INVALID_TYPE)
    if values don't the annotations. 

    Parameters
    ---------------
    fnc: Union[Callable, Class]
        Function to check parameters of or a class. If this
        is a class, then __init__ method is checked.
    """
    if isclass(func):
        func.__init__ = _enforce_annotations(func.__init__)
        return func

    checked_fnc = typechecked(func)
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return checked_fnc(*args, **kwargs)
        except TypeError as ex:
            raise DAFParameterError(str(ex), DAF_INVALID_TYPE) from ex

    return wrapper