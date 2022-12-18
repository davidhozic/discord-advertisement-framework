"""
    This modules contains functions and classes
    related to the console debug long or trace.
"""
from typing import Union
from enum import IntEnum, auto
import time
from threading import Lock
from .. import misc
try:
    from enum_tools.documentation import document_enum
except ImportError:
    document_enum = lambda x: x # This is only needed for documentation

__all__ = (
    "TraceLEVELS",
    "trace"
)

@document_enum
@misc.doc_category("Tracing")
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


@misc.doc_category("Tracing")
def trace(message: str,
          level: Union[TraceLEVELS, int] = TraceLEVELS.NORMAL):
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
        with GLOBALS.lock:
            timestruct = time.localtime()
            timestamp = "Date: {:02d}.{:02d}.{:04d} Time:{:02d}:{:02d}"
            timestamp = timestamp.format(timestruct.tm_mday,
                                        timestruct.tm_mon,
                                        timestruct.tm_year,
                                        timestruct.tm_hour,
                                        timestruct.tm_min)
            l_trace = f"{timestamp}\nTrace level: {level.name}\nMessage: {message}\n"
            print(l_trace)


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
            trace("[TRACING:] Could not find the requested trace level by name (string).", TraceLEVELS.WARNING)

    GLOBALS.set_level = level
