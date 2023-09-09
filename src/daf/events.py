"""
Module used to support listening and emitting events.
"""
from enum import Enum, auto
from typing import List, Dict, Callable, TYPE_CHECKING

from .misc.doc import doc_category
from .logging.tracing import TraceLEVELS, trace

import _discord as discord

if TYPE_CHECKING:
    from .message import BaseMESSAGE



__all__ = (
    "EventID",
    "add_listener",
    "remove_listener",
    "listen",
    "emit"
)


class GLOBAL:
    listeners: Dict[Enum, List[Callable]] = {}


@doc_category("Event reference")
class EventID(Enum):
    """
    Enum of all available events.
    """
    daf_startup = 0
    daf_shutdown = auto()
    message_ready = auto()
    discord_event = auto()


@doc_category("Event reference")
def add_listener(event: EventID, fnc: Callable):
    """
    Registers the function ``fnc`` as an event listener for ``event``.
    
    Parameters
    ------------
    event: EventID
        The event of listener to add.
    fnc: Callable
        The function listener to add.
    """
    listeners = GLOBAL.listeners[event] = GLOBAL.listeners.get(event, [])
    listeners.append(fnc)


@doc_category("Event reference")
def remove_listener(event: EventID, fnc: Callable):
    """
    Remove the function ``fnc`` from the list of listeners for ``event``.

    Parameters
    ------------
    event: EventID
        The event of listener to remove.
    fnc: Callable
        The function listener to remove.

    Raises
    ---------
    KeyError
        The event doesn't have any listeners.
    ValueError
        Provided function is not a listener.
    """
    GLOBAL.listeners[event].remove(fnc)


@doc_category("Event reference")
def listen(event: EventID):
    """
    Decorator used to register the function as an event listener.

    Parameters
    ---------------
    event: EventID
        The event that needs to occur for the function to be called.
    """
    def _listen_decor(fnc: Callable):
        add_listener(event, fnc)
        return fnc

    return _listen_decor


@doc_category("Event reference")
def emit(event: EventID, *args, **kwargs):
    """
    Emits an ``event`` by calling all the registered listener.

    Raises
    ---------
    TypeError
        Arguments provided don't match all the listener parameters.
    """
    trace(f"Emitting event {event}", TraceLEVELS.DEBUG)
    for listener in GLOBAL.listeners.get(event, []):
        listener(*args, **kwargs)


# Dummy event handlers for documenting each event.
@doc_category("Event reference")
def daf_startup():
    "Called when DAF has been initialized."


@doc_category("Event reference")
def daf_shutdown():
    "Called when DAF has finished shutting down"


@doc_category("Event reference")
def message_ready(message: "BaseMESSAGE"):
    """
    Called when message is ready to be sent.

    Parameters
    --------------
    message: BaseMESSAGE
        The message that is ready to be sent.
    """
