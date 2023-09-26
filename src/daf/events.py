"""
Module used to support listening and emitting events.
It also contains the event loop definitions.
"""
from contextlib import suppress
from enum import Enum, auto
from typing import Any, List, Dict, Callable, TypeVar, Coroutine, Set, Union

from .misc.doc import doc_category

import asyncio
import warnings

T = TypeVar('T')


__all__ = (
    "EventID",
    "EventController",
    "get_global_event_ctrl",
)


@doc_category("Event reference")
class EventID(Enum):
    """
    Enum of all available events.

    Global events (:func:`get_global_event_ctrl`) have a
    ``g_`` prefix on their name.
    """

    g_daf_startup = 0
    """
    Emitted at DAF startup.
    """

    g_daf_shutdown = auto()
    """
    Emitted at DAF shutdown.
    """
    g_trace = auto()
    """
    Emitted when :func:`~daf.logging.tracing.trace` is used.

    Parameters
    -----------
    level: :class:`~daf.logging.tracing.TraceLEVELS`
        The level of the trace.
    message: str
        The traced message.
    """
    g_account_expired = auto()
    """
    Emitted when account has been expired (token invalidated).
    
    Parameters
    -----------
    account: :class:`~daf.client.ACCOUNT
        The account that has been expired.
    """
    account_update = auto()

    message_ready = auto()
    message_removed = auto()
    message_added = auto()
    message_update = auto()

    server_removed = auto()
    server_added = auto()
    server_update = auto()
    auto_guild_start_join = auto()

    discord_member_join = auto()
    discord_invite_delete = auto()

    _dummy = auto()  # For stopping the event loop

    # Events for use externally (not within daf)
    _ws_disconnect = auto()


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


class EventController:
    def __init__(self) -> None:
        self.listeners: Dict[Enum, List[EventListener]] = {}
        self.event_queue = asyncio.Queue()
        self.loop_task: asyncio.Task = None
        self.running = False

    def start(self):
        """
        Starts the event loop.
        """
        if not self.running:
            self.clear_queue()
            self.loop_task = asyncio.create_task(self.event_loop())
            self.running = True
            # In case this is not the global controller, add itself to a list of non-global controllers
            # which will additionally receive any events emitted by the global controller.
            if self is not GLOBAL.g_controller:
                GLOBAL.non_global_controllers.add(self)

    def stop(self):
        "Stops event loop asynchronously"
        if self.running:
            self.running = False
            self.event_queue.put_nowait((EventID._dummy, tuple(), {}, asyncio.Future()))
            if self is GLOBAL.g_controller:
                return asyncio.gather(*[ctrl.stop() for ctrl in GLOBAL.non_global_controllers])

        return asyncio.gather(self.loop_task)

    def add_listener(self, event: EventID, fnc: Callable, predicate: Callable[[Any], bool] = None):
        """
        Registers the function ``fnc`` as an event listener for ``event``.
        
        Parameters
        ------------
        event: EventID
            The event of listener to add.
        fnc: Callable
            The function listener to add.
        """
        listeners = self.listeners[event] = self.listeners.get(event, [])
        listeners.append(EventListener(fnc, predicate))

    def remove_listener(self, event: EventID, fnc: Callable):
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
        with suppress(ValueError, KeyError):
            self.listeners[event].remove(fnc)

    def listen(self, event: EventID):
        """
        Decorator used to register the function as an event listener.

        Parameters
        ---------------
        event: EventID
            The event that needs to occur for the function to be called.
        """
        def _listen_decor(fnc: Callable):
            self.add_listener(event, fnc)
            return fnc

        return _listen_decor

    def emit(self, event: EventID, *args, **kwargs) -> asyncio.Future:
        """
        .. versionadded:: 3.0

        Emits an ``event`` by calling all the registered listeners.

        Returns
        ---------
        asyncio.Future
            A future object that can be awaited.
            You can use this to wait for the event to actually be processed.
            The result of the future will always be None.

        Raises
        ---------
        TypeError
            Arguments provided don't match all the listener parameters.
        """
        future = asyncio.Future()
        if not self.running:
            future.set_result(None)
            return future

        self.event_queue.put_nowait((event, args, kwargs, future))

        # If self is the global controller, also emit the event to other controllers.
        if GLOBAL.g_controller is self:
            future = asyncio.gather(
                future,
                *[
                    controller.emit(event, *args, **kwargs)
                    for controller in GLOBAL.non_global_controllers
                    if controller.running
                ]
            )  # Create a new future, that can be awaited for all event controllers to process an event

        return future
    
    def clear_queue(self):
        self.event_queue = asyncio.Queue()

    async def event_loop(self):
        """
        Event loop task.
        """
        queue = self.event_queue
        listeners = self.listeners

        event_id: EventID
        future: asyncio.Future

        while self.running:
            event_id, args, kwargs, future = await queue.get()

            for listener in listeners.get(event_id, [])[:]:
                try:
                    if listener.predicate is None or listener.predicate(*args, **kwargs):
                        if isinstance(r:= listener(*args, **kwargs), Coroutine):
                            await r

                except Exception as exc:
                    warnings.warn(f"({exc}) Could not call event handler {listener} for event {event_id}.")
                    future.set_exception(exc)
                    break


            if not future.done():  # In case exception was set
                future.set_result(None)

        if self is not GLOBAL.g_controller:
            GLOBAL.non_global_controllers.remove(self)

        self.clear_queue()


class GLOBAL:
    g_controller = EventController()
    non_global_controllers: Set["EventController"] = set()


def initialize():
    """
    Initializes the event module by creating the event loop task.
    Returns the event loop task, which's reference needs to be preserved.
    """
    GLOBAL.g_controller.start()


@doc_category("Event reference")
def get_global_event_ctrl() -> Union[EventController, None]:
    "Returns the global event controller"
    return GLOBAL.g_controller
