"""
    This module contains the class definitions for all things
    regarding the guild and also defines a USER class from the
    BaseGUILD class.
"""
from typing import Any, Coroutine, Union, List, Optional, Dict, Callable
from contextlib import suppress
from datetime import timedelta, datetime

from typeguard import typechecked

from ..message import *
from ..events import *
from ..logging.tracing import TraceLEVELS, trace
from ..misc import async_util, instance_track, doc, attributes
from .. import logging

import _discord as discord
import asyncio


__all__ = (
    "GUILD",
    "USER",
    "BaseGUILD",
)


class BaseGUILD:
    """
    .. versionchanged:: v3.0
        
        - Removed ``created_at`` property
        - New ``remove_after`` property
        

    Represents an universal guild.


    Parameters
    ---------------
    snowflake: Union[int, discord.Object]
        Discord's snowflake id or a Discord object that has the ID attribute.
    messages: Optional[List[MessageType]]
        List of messages to shill.
    generate_log: Optional[bool]
        Set to True if you wish to have message logs for this guild.
    remove_after: Optional[Union[timedelta, datetime]]
        Deletes the guild after:

        * timedelta - the specified time difference
        * datetime - specific date & time
    removal_buffer_length: Optional[int]
        Maximum number of messages to keep in the removed_messages buffer.

        .. versionadded:: 3.0
    """

    __slots__ = (
        "_apiobject",
        "logging",
        "_messages",
        "_remove_after",
        "removal_buffer_length",
        "_removed_messages",
        "parent",
        "_removal_timer_handle",
        "_event_ctrl",
    )

    _removed_messages: List[BaseMESSAGE]

    def __init__(
        self,
        snowflake: Any,
        messages: Optional[List] = None,
        logging: Optional[bool] = False,
        remove_after: Optional[Union[timedelta, datetime]] = None,
        removal_buffer_length: int = 50
    ) -> None:
        if messages is None:
            messages = []

        self._apiobject: discord.Object = snowflake
        self.logging: bool = logging
        # Contains all the different message objects (added in .initialize())
        self._messages: List[BaseMESSAGE] = messages
        self._remove_after = remove_after
        self.removal_buffer_length = removal_buffer_length
        self.parent = None
        self._removal_timer_handle: asyncio.Task = None
        self._event_ctrl = None
        attributes.write_non_exist(self, "_removed_messages", [])

    def __repr__(self) -> str:
        return f"{type(self).__name__}(discord={self._apiobject})"
    
    def __eq__(self, other: Any) -> bool:
        """
        Compares two guild objects if they're equal.
        """
        return isinstance(other, type(self)) and self.snowflake == other.snowflake

    @property
    def removed_messages(self) -> List[BaseMESSAGE]:
        "Returns a list of messages that were removed from server (last ``removal_buffer_length`` messages)."
        return self._removed_messages[:]

    @property
    def messages(self) -> List[BaseMESSAGE]:
        """
        Returns all the (initialized) message objects inside the object.

        .. versionadded:: v2.0
        """
        return self._messages[:]

    @property
    def snowflake(self) -> int:
        """
        .. versionadded:: v2.0

        Returns the discord's snowflake ID.
        """
        return (
            self._apiobject if isinstance(self._apiobject, int)
            else self._apiobject.id
        )

    @property
    def apiobject(self) -> discord.Object:
        """
        .. versionadded:: v2.4

        Returns the Discord API wrapper's object of self.
        """
        return self._apiobject
    
    @property
    def remove_after(self) -> Union[datetime, None]:
        "Returns the timestamp at which object will be removed or None if it will not be removed."
        return self._remove_after

    def add_message(self, message: BaseMESSAGE) -> asyncio.Future:
        """
        Adds a message to the message list.

        .. warning::
            To use this method, the guild must already be added to the
            framework's shilling list (or initialized).

        |ASYNC_API|

        Parameters
        --------------
        message: BaseMESSAGE
            Message object to add.

        Returns
        --------
        Awaitable
            An awaitable object which can be used to await for execution to finish.
            To wait for the execution to finish, use ``await`` like so: ``await method_name()``.

        Raises
        --------------
        TypeError
            Raised when the message is not of type the guild allows.
        Other
            Raised from message.initialize() method.
        """
        raise NotImplementedError

    @typechecked
    def remove_message(self, message: BaseMESSAGE) -> asyncio.Future:
        """
        Removes a message from the message list.

        |ASYNC_API|

        .. versionchanged:: 3.0

            The function is now async.

        Parameters
        --------------
        message: BaseMESSAGE
            Message object to remove.

        Returns
        --------
        Awaitable
            An awaitable object which can be used to await for execution to finish.
            To wait for the execution to finish, use ``await`` like so: ``await method_name()``.

        Raises
        --------------
        TypeError
            Raised when the message is not of type the guild allows.
        ValueError
            Raised when the message is not present in the list.
        """
        return self._event_ctrl.emit(EventID.message_removed, self, message)

    def update(self, init_options = None, **kwargs) -> asyncio.Future:
        """
        .. versionadded:: v2.0

        Used for changing the initialization parameters,
        the object was initialized with.

        |ASYNC_API|

        .. warning::
            Upon updating, the internal state of objects get's reset,
            meaning you basically have a brand new created object.
            It also resets the message objects.

        Parameters
        -------------
        **kwargs: Any
            Custom number of keyword parameters which you want to update,
            these can be anything that is available during the object creation.


        Returns
        --------
        Awaitable
            An awaitable object which can be used to await for execution to finish.
            To wait for the execution to finish, use ``await`` like so: ``await method_name()``.

        Raises
        -----------
        Union[TypeError, ValueError]
            Invalid keyword argument was passed.
        """
        return self._event_ctrl.emit(EventID.server_update, self, init_options, **kwargs)

    async def _init_messages(self):
        raise NotImplementedError

    # Non public
    @async_util.except_return
    async def initialize(self, parent: Any, event_ctrl: EventController, getter: Callable) -> None:
        """
        This function initializes the API related objects and
        then tries to initialize the MESSAGE objects.

        .. warning::
            This should NOT be manually called,
            it is called automatically after adding the message.

        .. versionchanged:: v2.4
            Added parent parameter to support multiple account
            structure.

        Parameters
        ------------
        parent: Any
            The parent object. (ACCOUNT)
        getter: Callable
            Callable function or async generator used for
            retrieving an api object (client.get_*).
        """
        self._event_ctrl = event_ctrl
        self.parent = parent
        _apiobject = getter(self.snowflake)

        if isinstance(_apiobject, Coroutine):
            try:
                _apiobject = await _apiobject
            except discord.HTTPException as exc:
                trace(f"Exception obtaining API object - {self}", TraceLEVELS.ERROR, exc, RuntimeError)

        if _apiobject is None:
            trace(f"Invalid ID {self.snowflake} - {self}", TraceLEVELS.ERROR, exception_cls=ValueError)
        
        self._apiobject = _apiobject
        if self._remove_after is not None:
            if isinstance(self._remove_after, timedelta):
                self._remove_after = datetime.now().astimezone() + self._remove_after
            else:
                self._remove_after = self._remove_after.astimezone()

            self._removal_timer_handle = (
                async_util.call_at(
                    event_ctrl.emit,
                    self._remove_after,
                    EventID.server_removed,
                    self
                )
            )

        event_ctrl.add_listener(EventID.message_ready, self._advertise, lambda server, m: server is self)
        event_ctrl.add_listener(EventID.message_removed, self._on_message_removed, lambda server, m: server is self)
        event_ctrl.add_listener(EventID.message_added, self._on_add_message, lambda server, m: server is self)
        event_ctrl.add_listener(EventID.server_update, self._on_update, lambda server, *h, **k: server is self)

        await self._init_messages()

    def generate_invite_log_context(self, member: discord.Member, invite_id: str) -> dict:
        raise NotImplementedError

    def generate_log_context(self) -> Dict[str, Union[str, int]]:
        """
        Generates a dictionary of the guild's context,
        which is then used for logging.

        Returns
        ---------
        Dict[str, Union[str, int]]
        """
        return {
            "name": self._apiobject.name,
            "id": self._apiobject.id,
            "type": type(self).__name__
        }

    # Event handlers
    async def _on_add_message(self, _, message: BaseMESSAGE):
        raise NotImplementedError

    async def _on_update(self, _, init_options, **kwargs):
        raise NotImplementedError

    async def _on_message_removed(self, _, message: BaseMESSAGE):
        trace(f"Removing message {message} from {self}", TraceLEVELS.NORMAL)
        self._messages.remove(message)
        self._removed_messages.append(message)
        if len(self._removed_messages) > self.removal_buffer_length:
            trace(f"Removing oldest record of removed messages {self._removed_messages[0]}", TraceLEVELS.DEBUG)
            del self._removed_messages[0]

        await message._close()

    @async_util.with_semaphore("update_semaphore")
    async def _advertise(self, _, message: BaseMESSAGE):
        """
        Common to all messages, function responsible for sending all the
        messages to this specific guild.

        This is an event handler.
        """
        guild_ctx = self.generate_log_context()
        author_ctx = self.parent.generate_log_context()

        if (message_context := await message._send()) and self.logging:
            await logging.save_log(guild_ctx, message_context, author_ctx)

        message._reset_timer()    

    async def _on_member_join(self, member: discord.Member):
        """
        Event listener that get's called when a member joins a guild.

        Parameters
        ---------------
        member: :class:`discord.Member`
            The member who joined the guild.
        """
        raise NotImplementedError

    async def _on_invite_delete(self, invite: discord.Invite):
        """
        Event listener that get's called when an invite has been deleted from a guild.

        Parameters
        --------------
        invite: :class:`discord.Invite`
            The invite that was deleted.
        """
        raise NotImplementedError

    @async_util.with_semaphore("update_semaphore")
    async def _close(self):
        """
        Cleans up and closes any asyncio related
        functionality.
        """
        if self._event_ctrl is None:  # Already closed
            return

        self._event_ctrl.remove_listener(EventID.message_ready, self._advertise)
        self._event_ctrl.remove_listener(EventID.message_removed, self._on_message_removed)
        self._event_ctrl.remove_listener(EventID.server_update, self._on_update)
        self._event_ctrl.remove_listener(EventID.message_added, self._on_add_message)
        for message in self.messages:
            await message._close()

        if self._removal_timer_handle is not None and not self._removal_timer_handle.cancelled():
            self._removal_timer_handle.cancel()
            await asyncio.gather(self._removal_timer_handle, return_exceptions=True)


@instance_track.track_id
@doc.doc_category("Guilds", path="guild")
@logging.sql.register_type("GuildTYPE")
class GUILD(BaseGUILD):
    """
    The GUILD object represents a server to which messages will be sent.

    .. versionchanged:: v3.0

        - Removed ``created_at`` property.
        - New ``remove_after`` property

    .. versionchanged:: v2.7

        Added ``invite_track`` parameter.

    Parameters
    ------------
    snowflake: Union[int, discord.Guild]
        Discord's snowflake ID of the guild or discord.Guild object.
    messages: Optional[List[Union[TextMESSAGE, VoiceMESSAGE]]]
        Optional list of TextMESSAGE/VoiceMESSAGE objects.
    logging: Optional[bool]
        Optional variable dictating whatever to log
        sent messages inside this guild.
    remove_after: Optional[Union[timedelta, datetime]]
        Deletes the guild after:

        * timedelta - the specified time difference
        * datetime - specific date & time

    invite_track: Optional[List[str]]
        .. versionadded:: 2.7

        List of invite IDs to be tracked for member join count inside the guild.
        **Bot account** only, does not work on user accounts.

        .. note::

            Accounts are required to have *Manage Channels* and *Manage Server* permissions inside a guild for
            tracking to fully function. *Manage Server* is needed for getting information about invite links,
            *Manage Channels* is needed to delete the invite from the list if it has been deleted,
            however tracking still works without it.

        .. warning::

            For GUILD to receive events about member joins, ``members`` intent is required to be True inside
            the ``intents`` parameters of :class:`daf.client.ACCOUNT`.
            This is a **privileged intent** that also needs to be enabled though Discord's developer portal for each bot.
            After it is enabled, you can set it to True .

            Invites intent is also needed. Enable it by setting ``invites`` to True inside
            the ``intents`` parameter of :class:`~daf.client.ACCOUNT`.
    removal_buffer_length: Optional[int]
        Maximum number of messages to keep in the removed_messages buffer.

        .. versionadded:: 3.0
    """
    __slots__ = (
        "update_semaphore",
        "join_count",
    )

    update_semaphore: asyncio.Semaphore

    @typechecked
    def __init__(self,
                 snowflake: Union[int, discord.Guild],
                 messages: Optional[List[Union[TextMESSAGE, VoiceMESSAGE]]] = None,
                 logging: Optional[bool] = False,
                 remove_after: Optional[Union[timedelta, datetime]] = None,
                 invite_track: Optional[List[str]] = None,
                 removal_buffer_length: int = 50):
        super().__init__(snowflake, messages, logging, remove_after, removal_buffer_length)
        if invite_track is None:
            invite_track = []

        # Auto strip any url parts and keep only ID by splitting
        self.join_count = {invite.split("/")[-1]: 0 for invite in invite_track}
        attributes.write_non_exist(self, "update_semaphore", asyncio.Semaphore(1))

    async def _get_invites(self) -> List[discord.Invite]:
        guild: discord.Guild = self.apiobject
        client: discord.Client = self.parent.client
        try:
            perms = guild.get_member(client.user.id).guild_permissions
            if perms.manage_guild:
                return await guild.invites()
        except discord.HTTPException as exc:
            trace(f"Error reading invite links for guild {guild.name}!", TraceLEVELS.ERROR, exc)

        return []  # Return empty on error or no permissions


    async def _init_messages(self):
        message: BaseChannelMessage
        for message in self._messages:
            if (await message.initialize(self, self._event_ctrl, self._get_guild_channels)) is not None:
                await self._on_message_removed(self, message)

    async def initialize(self, parent: Any, event_ctrl: EventController) -> None:
        """
        This function initializes the API related objects and
        then tries to initialize the MESSAGE objects.

        .. note::
            This should NOT be manually called, it is called automatically
            after adding the message.
        """
        if (exc := await super().initialize(parent, event_ctrl, parent.client.get_guild)) is not None:
            return exc

        # Fill invite counts
        if len(self.join_count):  # Skip invite query from Discord
            client: discord.Client = parent.client
            client.add_listener(self._discord_on_member_join, "on_member_join")
            client.add_listener(self._discord_on_invite_delete, "on_invite_delete")
            self._event_ctrl.add_listener(
                EventID.discord_member_join,
                self._on_member_join,
                predicate=lambda m: m.guild.id == self._apiobject.id
            )
            self._event_ctrl.add_listener(
                EventID.discord_invite_delete,
                self._on_invite_delete,
                predicate=lambda inv: inv.guild.id == self._apiobject.id
            )

            invites = await self._get_invites()
            invites = {invite.id: invite.uses for invite in invites}
            counts = self.join_count
            for invite in list(counts.keys()):
                try:
                    counts[invite] = invites[invite]
                except KeyError:
                    del counts[invite]
                    trace(
                        f"Invite link {invite} not found in {self.apiobject.name}. It will not be tracked!",
                        TraceLEVELS.ERROR
                    )

    def _get_guild_channels(self, *types):
        return set(x for x in self._apiobject.channels if isinstance(x, types))

    # API
    @typechecked
    def add_message(self, message: Union[TextMESSAGE, VoiceMESSAGE]):
        return self._event_ctrl.emit(EventID.message_added, self, message)

    def generate_invite_log_context(self, member: discord.Member, invite_id: str) -> dict:
        """
        Generates dictionary representing the log of a member joining a guild.

        Parameters
        ------------
        member: discord.Member
            The member that joined a guild.

        Returns
        ---------
        dict
            ::

                {
                    "id": ID of the invite,
                    "member": {
                        "id": Member ID,
                        "name": Member name
                    }
                }
        """
        return {
            "id": invite_id,
            "member": {
                "id": member.id,
                "name": member.name
            }
        }

    # Event Handlers
    async def _on_add_message(self, _, message: Union[TextMESSAGE, VoiceMESSAGE]):
        exc = await message.initialize(
            parent=self,
            event_ctrl=self._event_ctrl,
            channel_getter=self._get_guild_channels
        )
        if exc is not None:
            raise exc

        self._messages.append(message)
        with suppress(ValueError):  # Readd the removed message
            self._removed_messages.remove(message)

    async def _on_update(self, _, init_options, **kwargs):
        await self._close()
        try:
            # Update the guild
            if "snowflake" not in kwargs:
                kwargs["snowflake"] = self.snowflake

            if "invite_track" not in kwargs:
                kwargs["invite_track"] = list(self.join_count.keys())

            kwargs["messages"] = kwargs.pop("messages", self._messages)
            if init_options is None:
                init_options = {"parent": self.parent, "event_ctrl": self._event_ctrl}

            await async_util.update_obj_param(self, init_options=init_options, **kwargs)
        except Exception:
            await self.initialize(self.parent, self._event_ctrl)
            raise

    async def _on_member_join(self, member: discord.Member):        
        counts = self.join_count
        invites = await self._get_invites()
        invites = {invite.id: invite.uses for invite in invites}
        for id_, last_uses in counts.items():
            uses = invites[id_]
            if last_uses != uses:
                trace(f"User {member.name} joined to {member.guild.name} with invite {id_}", TraceLEVELS.DEBUG)
                counts[id_] = uses
                invite_ctx = self.generate_invite_log_context(member, id_)
                await logging.save_log(self.generate_log_context(), None, None, invite_ctx)
                return

    async def _on_invite_delete(self, invite: discord.Invite):
        if invite.id in self.join_count:
            del self.join_count[invite.id]
            trace(
                f"Invite link ID {invite.id} deleted from {self.apiobject.name} (ID: {self.apiobject.id})",
                TraceLEVELS.DEBUG
            )

    # Safety wrappers to make sure the event gets emitted through the event loop for safety
    async def _discord_on_member_join(self, member: discord.Member):
        self._event_ctrl.emit(EventID.discord_member_join, member)

    async def _discord_on_invite_delete(self, invite: discord.Invite):
        self._event_ctrl.emit(EventID.discord_invite_delete, invite)

    def _close(self):
        if self._event_ctrl is None:  # Already closed
            return

        client: discord.Client = self.parent.client
        # Removing these listeners doesn't require a mutex as it does not interfere
        # with any advertisement methods. These are only for processing
        # events on the PyCord API wrapper level.
        client.remove_listener(self._discord_on_member_join, "on_member_join")
        client.remove_listener(self._discord_on_invite_delete, "on_invite_delete")
        self._event_ctrl.remove_listener(EventID.discord_member_join, self._on_member_join)
        self._event_ctrl.remove_listener(EventID.discord_invite_delete, self._on_invite_delete)
        return super()._close()


@instance_track.track_id
@doc.doc_category("Guilds", path="guild")
@logging.sql.register_type("GuildTYPE")
class USER(BaseGUILD):
    """
    The USER object represents a user to whom messages will be sent.

    .. versionchanged:: v3.0

        - Removed ``created_at`` property.
        - New ``remove_after`` property

    .. versionchanged:: v2.7

        Added ``invite_track`` parameter.

    Parameters
    ------------
    snowflake: Union[int, discord.User]
        Discord's snowflake ID of the user or discord.User object.
    messages: Optional[List[DirectMESSAGE]]
        Optional list of DirectMESSAGE objects.
    logging: Optional[bool]
        Optional variable dictating whatever to log
        sent messages inside this guild.
    remove_after: Optional[Union[timedelta, datetime]]
        Deletes the user after:

        * timedelta - the specified time difference
        * datetime - specific date & time
    removal_buffer_length: Optional[int]
        Maximum number of messages to keep in the removed_messages buffer.

        .. versionadded:: 3.0
    """
    __slots__ = (
        "update_semaphore",
    )

    @typechecked
    def __init__(
        self,
        snowflake: Union[int, discord.User],
        messages: Optional[List[DirectMESSAGE]] = None,
        logging: Optional[bool] = False,
        remove_after: Optional[Union[timedelta, datetime]] = None,
        removal_buffer_length: int = 50
    ) -> None:
        super().__init__(snowflake, messages, logging, remove_after, removal_buffer_length)
        attributes.write_non_exist(self, "update_semaphore", asyncio.Semaphore(1))

    @typechecked
    def add_message(self, message: DirectMESSAGE) -> asyncio.Future:
        return self._event_ctrl.emit(EventID.message_added, self, message)

    def _check_state(self) -> bool:
        """
        Checks if the user is ready to be deleted.

        Returns
        ----------
        True
            The user should be deleted.
        False
            The user is in proper state, do not delete.
        """
        return super()._check_state()

    async def _init_messages(self):
        message: DirectMESSAGE
        for message in self._messages:
            if (await message.initialize(self, self._event_ctrl, self._apiobject)) is not None:
                await self._on_message_removed(self, message)

    async def initialize(self, parent: Any, event_ctrl: EventController):
        """
        This function initializes the API related objects and
        then tries to initialize the MESSAGE objects.
        """
        return await super().initialize(
            parent,
            event_ctrl,
            parent.client.get_or_fetch_user
        )

    # Event Handlers
    async def _on_add_message(self, _, message: Union[VoiceMESSAGE, VoiceMESSAGE]):
        exc = await message.initialize(parent=self, event_ctrl=self._event_ctrl, guild=self._apiobject)
        if exc is not None:
            raise exc

        self._messages.append(message)
        with suppress(ValueError):  # Readd the removed message
            self._removed_messages.remove(message)

    async def _on_update(self, _, init_options, **kwargs):
        try:
            # Update the guild
            await self._close()
            if "snowflake" not in kwargs:
                kwargs["snowflake"] = self.snowflake

            kwargs["messages"] = kwargs.pop("messages", self._messages)

            if init_options is None:
                init_options = {"parent": self.parent, "event_ctrl": self._event_ctrl}

            await async_util.update_obj_param(self, init_options=init_options, **kwargs)
        except Exception:
            await self.initialize(self.parent, self._event_ctrl)
            raise
