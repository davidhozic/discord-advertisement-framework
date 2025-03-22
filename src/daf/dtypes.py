"""
    The module contains definitions regarding the data types
    you can send using the xxxMESSAGE objects.
"""
from typing import Callable

from .logging.tracing import *


__all__ = (
    "data_function",
)


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
        "Using @data_function is deprecated and its usage is no longer allowed. Use DynamicMessageData / DynamicMessageData instead.",
        TraceLEVELS.ERROR,
        exception_cls=NameError
    )
