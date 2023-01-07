"""
    This modules contains functions and classes
    related to the console debug long or trace.
"""
from typing import Union, Optional
from enum import IntEnum, auto
from threading import Lock
from datetime import datetime
from sys import _getframe

from .. import misc

try:
    from enum_tools.documentation import document_enum
except ImportError:
    document_enum = lambda x: x # This is only needed for documentation

__all__ = (
    "TraceLEVELS",
    "trace"
)


C_TRACE_FORMAT = \
"""
Date: {date}
Level: {level}
Reason: {reason}
Message: [{module}] {message}
"""

@document_enum
@misc.doc_category("Logging reference")
class TraceLEVELS(IntEnum):
    """
    Levels of trace for debug.

    .. seealso:: :ref:`trace`

    .. versionchanged:: v2.3
        Added DEPRECATION
    """
    
    DEPRECATED = 0
    """
    Show only deprecation notices.
    """
    ERROR = auto()
    """
    Show deprecations and errors.
    """
    WARNING = auto()
    """
    Show deprecations, errors, warnings.
    """
    NORMAL = auto()
    """
    Show deprecations, errors, warnings, info messages.
    """
    DEBUG = auto()
    """
    Show deprecations, errors, warnings, info messages, debug messages.
    """


class GLOBALS:
    """Storage class used for storing global variables of the module."""
    set_level = TraceLEVELS.DEPRECATED
    lock = Lock() # For print thread safety


@misc.doc_category("Logging reference")
def trace(message: str,
          level: Union[TraceLEVELS, int] = TraceLEVELS.NORMAL,
          reason: Optional[str] = None):
    """
    | Prints a trace to the console.
    | This is thread safe.

    .. versionchanged:: v2.3
        
        .. card::
        
            Will only print if the level is lower than the configured
            (thru :func:`~daf.core.run`'s debug parameter max level.

            Eg. if the max level is :class:`~daf.logging.tracing.TraceLEVELS.ERROR`, then the 
            level parameter needs to be either :class:`~daf.logging.tracing.TraceLEVELS.DEPRECATED`
            or :class:`~daf.logging.tracing.TraceLEVELS.ERROR`, 
            else nothing will be printed.

    
    Parameters
    --------------
    message: str
        Trace message.
    level: TraceLEVELS | int
        Level of the trace. Defaults to TraceLEVELS.NORMAL.
    """
    if GLOBALS.set_level >= level:
        frame = _getframe(1)
        module = frame.f_globals["__name__"]
        msg = C_TRACE_FORMAT.format(
                date=datetime.now().isoformat(sep=' '),
                level=level.name,
                reason=reason,
                module=module,
                message=message
        )
        with GLOBALS.lock:
            print(msg)


def initialize(level: Union[TraceLEVELS, int, str]):
    """
    Initializes the tracing module

    .. versionchanged:: v2.3
        Changed the parameter from
        enable: bool to level: TraceLEVELS | int | str.

    Parameters
    ------------
    level: TraceLEVELS | int | str
        The level of tracing to be displayed.
        The bigger the value, more detailed everything will be.
    """
    if isinstance(level, str):
        for name, val in vars(TraceLEVELS).items():
            if name == level:
                level = val
                break
        else:
            trace("Could not find the requested trace level by name (string).", TraceLEVELS.WARNING)

    GLOBALS.set_level = level
