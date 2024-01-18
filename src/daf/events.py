"""
Module used to support listening and emitting events.
It also contains the event loop definitions.
"""
from enum import Enum, auto

from .misc.doc import doc_category
from asyncio_event_hub import EventController


__all__ = (
    "EventID",
    "EventController",
    "get_global_event_ctrl",
)


class GLOBAL:
    g_controller = EventController()


def initialize():
    """
    Initializes the event module by creating the event loop task.
    Returns the event loop task, which's reference needs to be preserved.
    """
    GLOBAL.g_controller.start()


@doc_category("Event reference")
def get_global_event_ctrl() -> EventController:
    "Returns the global event controller"
    return GLOBAL.g_controller


@doc_category("Event reference")
class EventID(Enum):
    """
    Enum of all available events.

    Global events (:func:`get_global_event_ctrl`) have a
    ``g_`` prefix on their name. Other events are controlled by account bound :class:`daf.events.EventController`.
    """
    # Global events
    g_daf_startup = 0
    g_daf_shutdown = auto()
    g_trace = auto()
    g_account_expired = auto()

    # Events that trigger internal actions
    # (for safety reasons)
    _trigger_account_update = auto()

    _trigger_message_ready = auto()
    _trigger_message_remove = auto()
    _trigger_message_add = auto()
    _trigger_message_update = auto()

    _trigger_server_remove = auto()
    _trigger_server_add = auto()
    _trigger_server_update = auto()
    _trigger_auto_guild_start_join = auto()

    _trigger_auto_responder_add = auto()
    _trigger_auto_responder_remove = auto()

    # Finished action events
    message_removed = auto()

    # Discord related events
    discord_member_join = auto()
    discord_invite_delete = auto()
    discord_guild_join = auto()
    discord_guild_remove = auto()
    discord_message = auto()

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
