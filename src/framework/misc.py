"""
    This module contains definitions regarding miscellaneous
    items that can appear in multiple modules
"""

from typing import Coroutine, Callable, Any

###############################
# Safe access functions
###############################
def _write_safe_vars(obj: Any, name: str, value: Any, overwrite: bool=False):
    """
    Creates a reference for an attribute that can only be changed if overwrite parameter is True
    or if the reference doesn't exist. This is to protect some variables from being modified in the .update method.


    Parameters
    -------------
    obj: Any
        Object to safely write.
    
    name: str
        The name of the attribute to change.

    value: Any
        The value to change the attribute with.
    
    overwrite: bool
        Set this to True to allow the variable to be re-referenced.
        If False, then variables with existing references will be left alone.
    """

    # TODO: Test if it works
    if overwrite or not hasattr(obj, name): # Write only if forced, or if not forced, then the attribute must not exist
        setattr(obj, name, value)



###########################
# Decorators
###########################
# TODO: Change Lock to semaphore, add parameter that dictates how many to take
def _async_safe(lock: str) -> Callable:
    """
    Function that returns a safety decorator, which uses the :strong:`lock` parameter
    as a safety mechanism.

    This is for usage on :strong:`methods`

    Returns
    --------------
    Returns the safety decorator.

    Raises
    --------------
    TypeError
        The ``lock`` parameter is not a string describing the lock attribute of a table.
    """

    def __safe_access(coroutine: Coroutine) -> Coroutine:
        """
        Decorator that returns a method wrapper Coroutine that utilizes a
        asyncio lock to assure safe asynchronous operations.
        """
        async def wrapper(self, *args, **kwargs):
            async with getattr(self, lock):
                return await coroutine(self, *args, **kwargs)
        
        wrapper.__annotations__ = coroutine.__annotations__ # Keep the same type hints

        return wrapper


    if type(lock) is not str:
        raise TypeError("lock parameter must be an attribute name of the asyncio lock inside the object")

    return __safe_access