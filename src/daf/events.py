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
