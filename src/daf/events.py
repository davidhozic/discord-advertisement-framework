"""
Module used to support listening and emitting events.
It also contains the event loop definitions.
"""
from contextlib import suppress, asynccontextmanager
from enum import Enum, auto
from typing import Any, List, Dict, Callable, TypeVar, Coroutine, Set, Union
from sys import _getframe

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
class EventController:
    """
    Responsible for controlling the event loop, listening and emitting events.
    """
    def __init__(self) -> None:
        self.listeners: Dict[Enum, List[EventListener]] = {}
        self.event_queue = asyncio.Queue()
        self.loop_task: asyncio.Task = None
        self.running = False
        self._critical_lock = asyncio.Lock()

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

    @asynccontextmanager
    async def critical(self):
        """
        Asynchronous Context manager (``async with`` statement), that prevents
        any events from being processed until this critical section is exited.
        """
        await self._critical_lock.acquire()
        yield
        self._critical_lock.release()

    def stop(self):
        "Stops event loop asynchronously"
        if self.running:
            self.running = False
            self.event_queue.put_nowait((EventID._dummy, tuple(), {}, asyncio.Future()))
            if self is GLOBAL.g_controller:
                return asyncio.gather(*[ctrl.stop() for ctrl in GLOBAL.non_global_controllers])

        return asyncio.gather(self.loop_task)

    def add_listener(self, event: "EventID", fnc: Callable, predicate: Callable[[Any], bool] = None):
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

    def remove_listener(self, event: "EventID", fnc: Callable):
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

    def listen(self, event: "EventID"):
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

    def emit(self, event: "EventID", *args, **kwargs) -> asyncio.Future:
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
            caller_frame = _getframe(1)
            caller_info = caller_frame.f_code
            caller_text = f"{caller_info.co_name} ({caller_info.co_filename})"
            warnings.warn(
                f"{self} is not running, but {event} was emitted, which was ignored! Caller: {caller_text}",
                stacklevel=2
            )
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
            async with self._critical_lock:
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


@doc_category("Event reference")
class EventID(Enum):
    """
    Enum of all available events.

    Global events (:func:`get_global_event_ctrl`) have a
    ``g_`` prefix on their name. Other events are controlled by account bound :class:`daf.events.EventController`.
    """

    g_daf_startup = 0
    g_daf_shutdown = auto()
    g_trace = auto()
    g_account_expired = auto()

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


@doc_category("Event reference")
async def g_daf_startup():
    """
    Event that is emitted after DAF has started.
    """

@doc_category("Event reference")
async def g_daf_shutdown():
    """
    Event that is emitted after DAF has shutdown.
    """

@doc_category("Event reference")
async def g_trace(level, message: str):
    """
    Event that is emitted when a message has been printed with :func:`~daf.logging.tracing.trace`.

    :param level: The trace detail.
    :type level: TraceLEVELS
    :param message: The message traced.
    :type message: str
    """

@doc_category("Event reference")
async def g_account_expired(account):
    """
    Event that is emitted when an account has it's token invalidated
    and is being forcefully removed.

    :param account: The account updated
    :type account: daf.client.ACCOUNT
    """

@doc_category("Event reference")
async def account_update(account):
    """
    Event that is emitted before an account update.

    :param account: The account updated
    :type account: daf.client.ACCOUNT
    """

@doc_category("Event reference")
async def message_ready(guild, message):
    """
    Event that is emitted when the message is ready to be sent.

    :param guild: The guild message belongs to.
    :type guild: daf.guild.GUILD
    :param message: The message that is ready. 
    :type message: daf.message.TextMESSAGE
    """

@doc_category("Event reference")
async def message_removed(guild, message):
    """
    Event that is emitted before the message is be removed.

    :param guild: The guild message belongs to.
    :type guild: daf.guild.GUILD
    :param message: The message removed.
    :type message: daf.message.TextMESSAGE
    """

@doc_category("Event reference")
async def message_added(guild, message):
    """
    Event that is emitted before the message is added.

    :param guild: The guild message belongs to.
    :type guild: daf.guild.GUILD
    :param message: The message added.
    :type message: daf.message.TextMESSAGE
    """

@doc_category("Event reference")
async def message_update(guild, message):
    """
    Event that is emitted before the message is updated.

    :param guild: The guild message belongs to.
    :type guild: daf.guild.GUILD
    :param message: The message updated.
    :type message: daf.message.TextMESSAGE
    """


@doc_category("Event reference")
async def server_removed(server):
    """
    Event that is emitted before the server is be removed.

    :param server: The server removed.
    :type server: daf.guild.GUILD | daf.guild.USER | daf.guild.AutoGUILD
    """

@doc_category("Event reference")
async def server_added(server):
    """
    Event that is emitted before the server is added.

    :param server: The server added.
    :type server: daf.guild.GUILD | daf.guild.USER | daf.guild.AutoGUILD
    """

@doc_category("Event reference")
async def server_update(server):
    """
    Event that is emitted before the server is updated.

    :param server: The server updated.
    :type server: daf.guild.GUILD | daf.guild.USER | daf.guild.AutoGUILD
    """

@doc_category("Event reference")
async def auto_guild_start_join(auto_guild):
    """
    Event that is emitted when the join for new server should start.

    :param auto_guild: The AutoGUILD responsible for the new server join.
    :type auto_guild: daf.guild.AutoGUILD
    """
