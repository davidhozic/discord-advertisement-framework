"""
    The module contains definitions regarding the data types
    you can send using the xxxMESSAGE objects.
"""
from typing import Any, Callable, Coroutine, Union, Optional
from functools import wraps

from .logging.tracing import *
from .misc import doc

import importlib.util as iu
import io


__all__ = (
    "data_function",
    "_FunctionBaseCLASS",
)


class GLOBALS:
    "Storage class used for storing global variables"
    


#######################################################################
# Decorators
#######################################################################
class _FunctionBaseCLASS:
    """
    Used as a base class to FunctionCLASS which gets created in :ref:`data_function` decorator.
    Because the FunctionCLASS is inaccessible outside the :ref:`data_function` decorator,
    this class is used to detect if the MESSAGE.data parameter is of function type,
    because the function isinstance also returns True when comparing
    the object to it's class or to the base class from which the object class is inherited from.
    """


def data_function(fnc: Callable):
    """
    Decorator used for wrapping a function that will return data to send when the message is ready.

    The ``fnc`` function must return data that is of type that the **x**\\ MESSAGE object supports.
    **If the type returned is not valid, the send attempt will simply be ignored and nothing will be logged at at**,
    this is useful if you want to use the ``fnc`` function to control whenever the message is ready to be sent.
    For example: if we have a function defined like this:

    .. code-block::
        :emphasize-lines: 3

        @daf.data_function
        def get_data():
            return None

        ...
        daf.TextMESSAGE(..., data=get_data())
        ...

    then no messages will ever be sent,
    nor will any logs be made since invalid values are simply ignored by the framework.



    Parameters
    ------------
    fnc: Callable
        The function to wrap.

    Returns
    -----------
    FunctionCLASS
        A class for creating wrapper objects is returned. These wrapper objects can be used as
        a ``data`` parameter to the :ref:`Messages` objects.
    """
    trace(
        "Using @data_function is deprecated. Use DynamicMessageData / DynamicMessageData instead.",
        TraceLEVELS.DEPRECATED
    )

    @wraps(fnc, updated=[])
    class FunctionCLASS(_FunctionBaseCLASS):
        """
        Used for creating special classes that are then used to create objects in the daf.MESSAGE
        data parameter, allows for sending dynamic content received thru an user defined function.

        Parameters
        -----------
        - Custom number of positional and keyword arguments.

        .. literalinclude:: ../../Examples/Message Types/TextMESSAGE/main_data_function.py
            :language: python
        """
        __slots__ = (
            "args",
            "kwargs",
            "func_name",
        )

        def __init__(self, *args: Any, **kwargs: Any):
            self.fnc = fnc
            self.args = args
            self.kwargs = kwargs
            self.func_name = fnc.__name__

        async def retrieve(self):
            """
            Retrieves the data from the user function.
            """
            _ = fnc(*self.args, **self.kwargs)
            if isinstance(_, Coroutine):
                return await _
            return _

        def __str__(self) -> str:
            return self.func_name

    return FunctionCLASS


#######################################################################
# Other
#######################################################################
