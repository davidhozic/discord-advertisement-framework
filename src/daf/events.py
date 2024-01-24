"""
Module used to support listening and emitting events.
It also contains the event loop definitions.
"""
from asyncio_event_hub import EventController
from enum import Enum, auto



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


def get_global_event_ctrl() -> EventController:
    "Returns the global event controller"
    return GLOBAL.g_controller


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
