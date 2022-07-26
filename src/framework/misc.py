"""
    This module contains definitions regarding miscellaneous
    items that can appear in multiple modules
"""

from typing import Coroutine, Callable, Any, Optional
from asyncio import Semaphore


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

    # TODO: Test if it works
    if not hasattr(obj, name): # Write only if forced, or if not forced, then the attribute must not exist
        setattr(obj, name, value)



###########################
# Decorators
###########################
# TODO: Change Lock to semaphore, add parameter that dictates how many to take
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


    if type(semaphore) is not str:
        raise TypeError("semaphore parameter must be an attribute name of the asyncio semaphore inside the object")

    return __safe_access