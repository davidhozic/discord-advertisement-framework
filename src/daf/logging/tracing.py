"""
    This modules contains functions and classes
    related to the console debug long or trace.
"""
from typing import Union, Optional
from enum import Enum, auto
from threading import current_thread, Thread
from datetime import datetime
from sys import _getframe

from ..misc import doc
from ..events import get_global_event_ctrl, EventID

try:
    from enum_tools.documentation import document_enum
except ImportError:
    def x(x): return x  # This is only needed for documentation
    document_enum = x

import asyncio


__all__ = (
    "TraceLEVELS",
    "trace"
)


C_TRACE_FORMAT = "[{date}] ({level}) | {module}: {message} ({reason})"


@document_enum
@doc.doc_category("Logging reference")
class TraceLEVELS(Enum):
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

    def __ge__(self, __value: "TraceLEVELS") -> bool:
        return self.value >= __value.value


TRACE_COLOR_MAP = {
    TraceLEVELS.DEPRECATED: "\u001b[30m",
    TraceLEVELS.ERROR: "\u001b[31m",
    TraceLEVELS.WARNING: "\u001b[33m",
    TraceLEVELS.NORMAL: "\u001b[37m",
    TraceLEVELS.DEBUG: "\u001b[36m",
}


class GLOBALS:
    """Storage class used for storing global variables of the module."""
    set_level = TraceLEVELS.DEPRECATED
    loop_thread: Thread = None
    loop: asyncio.AbstractEventLoop = None


@doc.doc_category("Logging reference")
def trace(message: str,
          level: Union[TraceLEVELS, int] = TraceLEVELS.NORMAL,
          reason: Optional[Exception] = None,
          exception_cls: Optional[Exception] = None):
    """
    Prints a trace to the console.
    This is thread safe.

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
    reason: Optional[Exception]
        Optional exception object, which caused the prinout.
    exception_cls: Optional[Exception]
        An exception to raise after tracing.
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

        if current_thread() is GLOBALS.loop_thread:  # Thread-safe
            evt = get_global_event_ctrl()
            evt.emit(EventID.g_trace, level, message)
            print(TRACE_COLOR_MAP[level] + msg + "\033[0m")
        elif GLOBALS.loop is not None:
            GLOBALS.loop.call_soon_threadsafe(trace, message, level, reason)

        if exception_cls is not None:
            raise exception_cls(message) from reason


def initialize(level: Union[TraceLEVELS, int, str] = TraceLEVELS.NORMAL):
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

    GLOBALS.loop_thread = current_thread()
    GLOBALS.set_level = level
    GLOBALS.loop = asyncio.get_running_loop()
