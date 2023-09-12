"""
Module used to support listening and emitting events.
It also contains the event loop definitions.
"""
from contextlib import suppress
from enum import Enum, auto
from typing import Any, List, Dict, Callable, TYPE_CHECKING, TypeVar, Coroutine

from .misc.doc import doc_category
from .logging.tracing import TraceLEVELS, trace

import asyncio
import _discord as discord

if TYPE_CHECKING:
    from .message import BaseMESSAGE


T = TypeVar('T')



__all__ = (
    "EventID",
    "add_listener",
    "remove_listener",
    "emit",
    "listen"
)


class GLOBAL:
    listeners: Dict[Enum, List["EventListener"]] = {}
    event_queue = asyncio.Queue()


class EventListener:
    def __init__(self, fnc: Callable, predicate: Callable[[T], bool] = None) -> None:
        self.fnc = fnc
        self.predicate = predicate

    def __eq__(self, o):
        return (isinstance(o, EventListener) and self.fnc is o.fnc) or o == self.fnc

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        return self.fnc(*args, **kwds)

    def __hash__(self) -> int:
        return hash(self.fnc)


@doc_category("Event reference")
class EventID(Enum):
    """
    Enum of all available events.
    """
    daf_startup = 0
    daf_shutdown = auto()
    message_ready = auto()
    trace = auto()
    account_expired = auto()
    guild_expired = auto()
    _stop_event_loop = auto()


@doc_category("Event reference")
def add_listener(event: EventID, fnc: Callable, predicate: Callable[[T], bool] = None):
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
    listeners.append(EventListener(fnc, predicate))


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
    with suppress(ValueError):
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
    GLOBAL.event_queue.put_nowait((event, args, kwargs))


def initialize():
    """
    Initializes the event module by creating the event loop task.
    Returns the event loop task, which's reference needs to be preserved.
    """
    return asyncio.create_task(event_loop())


async def event_loop():
    """
    Event loop task.
    """
    queue = GLOBAL.event_queue
    listeners = GLOBAL.listeners
    while True:
        event_id, args, kwargs = await queue.get()

        for listener in listeners.get(event_id, []):
            if listener.predicate is None or listener.predicate(*args, **kwargs):
                if isinstance(r:= listener(*args, **kwargs), Coroutine):
                    await r

        if event_id is EventID._stop_event_loop:
            break


# Dummy event handlers for documenting each event.
@doc_category("Event reference")
def on_daf_startup():
    "Called when DAF has been initialized."


@doc_category("Event reference")
def on_daf_shutdown():
    "Called when DAF has finished shutting down"


@doc_category("Event reference")
def on_message_ready(message: "BaseMESSAGE"):
    """
    Called when message is ready to be sent.

    Parameters
    --------------
    message: BaseMESSAGE
        The message that is ready to be sent.
    """

@doc_category("Event reference")
def on_trace(content: str):
    """
    Called when an trace to the console has been issued.

    Parameters
    ----------
    content: str
        The content being traced.
    """
