"""
Automatic GUILD generation.
"""
from __future__ import annotations
from typing import Any, Union, List, Optional, Dict
from datetime import timedelta, datetime
from typeguard import typechecked
from contextlib import suppress
from copy import deepcopy

from ..misc import async_util, instance_track, doc, attributes
from ..logging.tracing import TraceLEVELS, trace
from ..message import BaseChannelMessage
from ..logic import BaseLogic
from ..events import *
from ..logic import *

from .guilduser import GUILD
from .. import logging
from .. import web

import _discord as discord
import asyncio
import re


GUILD_JOIN_INTERVAL = timedelta(seconds=45)
GUILD_MAX_AMOUNT = 100


class MessageDuplicator:
    """
    Used for duplicating messages tracking message references.
    Messages that have 0 message references left are removed
    """
    def __init__(self, message: BaseChannelMessage) -> None:
        self.message = message
        self.count = 0
        self.copied = False

    def duplicate(self) -> BaseChannelMessage:
        copy = deepcopy(self.message)
        self.count += 1
        self.copied = True
        return copy
    
    def deduplicate(self):
        self.count -= 1

    def __eq__(self, other: Union[BaseChannelMessage, MessageDuplicator]):
        if isinstance(other, MessageDuplicator):
            return other.message == self.message

        return other == self.message

    @property
    def pending_removal(self) -> bool:
        return self.copied and not self.count  # Copied at least once and no copies left


@instance_track.track_id
@doc.doc_category("Auto objects", path="guild")
class AutoGUILD:
    """

    .. versionchanged:: v4.0.0

        - Restored original way AutoGUILD
          works (as a GUILD generator)
        - Include and exclude patterns now accept a daf.logic.BaseLogic
          object for more flexible matching. Using strings (text) is deprecated
          and will be removed.

    Represents multiple guilds (servers) based on a text pattern.
    AutoGUILD generates :class:`daf.guild.GUILD` objects for each matched pattern.

    Parameters
    --------------
    include_pattern: BaseLogic
        Matching condition, which checks if the name of guilds matches defined condition.
    remove_after: Optional[Union[timedelta, datetime]] = None
        When to remove this object from the shilling list.
    messages: List[BaseChannelMessage]
        List of messages with channels. This includes TextMESSAGE and VoiceMESSAGE.
    logging: Optional[bool] = False
        Set to True if you want the guilds generated to log
        sent messages.
    auto_join: Optional[web.GuildDISCOVERY] = None
        .. versionadded:: v2.5

        Optional :class:`~daf.web.GuildDISCOVERY` object which will automatically discover
        and join guilds though the browser.
        This will open a Google Chrome session.
    invite_track: Optional[List[str]]
        List of invite links (or invite codes) to track.
    removal_buffer_length: int
        The size of removed messages buffer.
        A message is added to this buffer when remove_message is called by the user or a message
        automatically removes itself for any reason.
        Defaults to 50.
    """
    __slots__ = (
        "include_pattern",
        "_remove_after",
        "logging",
        "update_semaphore",
        "parent",
        "auto_join",
        "guild_query_iter",
        "guild_join_count",
        "_messages",
        "removal_buffer_length",
        "_removal_timer_handle",
        "_guild_join_timer_handle",
        "_invite_join_count",
        "_cache",
        "_event_ctrl",
    )

    @typechecked
    def __init__(
        self,
        include_pattern: Union[BaseLogic, str],
        exclude_pattern: Optional[str] = None,
        remove_after: Optional[Union[timedelta, datetime]] = None,
        messages: Optional[List[BaseChannelMessage]] = None,
        logging: Optional[bool] = False,
        auto_join: Optional[web.GuildDISCOVERY] = None,
        invite_track: Optional[List[str]] = None,
        removal_buffer_length: int = 50
    ) -> None:
        if messages is None:
            messages = []

        if invite_track is None:
            invite_track = []

        if isinstance(include_pattern, str):
            trace(
                "Using text (str) on 'include_pattern' parameter of AutoGUILD is deprecated (planned for removal in 4.2.0)!\n"
                "Use logical operators instead (daf.logic). E. g., regex, contains, or_, ...\n",
                TraceLEVELS.DEPRECATED
            )
            include_pattern = regex(re.sub(r"\s*\|\s*", '', include_pattern))

        if exclude_pattern is not None:
            trace(
                "'exclude_pattern' parameter is deprecated (planned for removal in 4.2.0)!\n",
                TraceLEVELS.DEPRECATED
            )
            exclude_pattern = regex(re.sub(r"\s*\|\s*", '', exclude_pattern))
            include_pattern = and_(include_pattern, not_(exclude_pattern))

        self.include_pattern = include_pattern
        self._remove_after = remove_after
        self._messages: List[MessageDuplicator] = []
        self.logging = logging
        self.auto_join = auto_join
        self.parent = None
        self.guild_query_iter = None
        self.guild_join_count = 0
        self.removal_buffer_length = removal_buffer_length
        self._removal_timer_handle: asyncio.Task = None
        self._guild_join_timer_handle: asyncio.Task = None
        self._cache: List[GUILD] = []
        self._event_ctrl: EventController = None

        for message in messages:
            self.add_message(message)

        self._invite_join_count = {invite.split("/")[-1]: 0 for invite in invite_track}
        attributes.write_non_exist(self, "update_semaphore", asyncio.Semaphore(1))

    def __repr__(self) -> str:
        return f"AutoGUILD(include_pattern='{self.include_pattern}'"

    @property
    def messages(self) -> List[BaseChannelMessage]:
        """
        .. versionadded:: 3.0

        Returns all the (template) message objects.
        """
        return [x.message for x in self._messages]

    @property
    def guilds(self) -> List[GUILD]:
        "Returns cached GUILD objects."
        return self._cache

    @property
    def remove_after(self) -> Union[datetime, None]:
        "Returns the timestamp at which AutoGUILD will be removed or None if it will never be removed."
        return self._remove_after

    def _get_guilds(self):
        "Returns all the guilds that match the include_pattern"
        client: discord.Client = self.parent.client
        guilds = [
            g for g in client.guilds
            if self.include_pattern.check(g.name.lower())
        ]
        return guilds

    # API
    @typechecked
    def add_message(self, message: BaseChannelMessage) -> asyncio.Future:
        """
        Adds a message to the message list.

        .. warning::
            To use this method, the guild must already be added to the
            framework's shilling list (or initialized).

        |ASYNC_API|

        Parameters
        --------------
        message: BaseChannelMessage
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
        message._update_tracked_id(False)  # Don't allow remote operations, but still track
        message.parent = self  # Since it won't be "initialized", set parent here
        duplicator = MessageDuplicator(message)
        self._messages.append(duplicator)
        return asyncio.gather(*(g.add_message(duplicator.duplicate()) for g in self._cache))

    @typechecked
    def remove_message(self, message: BaseChannelMessage) -> asyncio.Future:
        """
        Remove a ``message`` from the advertising list.

        |ASYNC_API|

        Parameters
        --------------
        message: BaseChannelMessage
            Message object to remove.

        Returns
        --------
        Awaitable
            An awaitable object which can be used to await for execution to finish.
            To wait for the execution to finish, use ``await`` like so: ``await method_name()``.
        """
        self._messages.remove(message)  # Remove duplicator
        futures = []
        for g in self._cache:
            with suppress(ValueError):
                # Get the copied message index, all deep copied messages compare True, if they
                # were copied from the same source message.
                idx = g._messages.index(message)
                futures.append(g.remove_message(g._messages[idx]))

        return asyncio.gather(*futures)

    def update(self, init_options = None, **kwargs) -> asyncio.Future:
        """
        Updates the object with new initialization parameters.

        |ASYNC_API|

        Returns
        --------
        Awaitable
            An awaitable object which can be used to await for execution to finish.
            To wait for the execution to finish, use ``await`` like so: ``await method_name()``.

        .. WARNING::
            After calling this method the entire object is reset
            (this includes it's GUILD objects in cache).
        """
        return self._event_ctrl.emit(EventID._trigger_server_update, self, init_options, **kwargs)

    # Non public methods
    def _reset_auto_join_timer(self):
        "Resets the periodic auto guild join timer."
        self._guild_join_timer_handle = async_util.call_at(
            self._event_ctrl.emit,
            GUILD_JOIN_INTERVAL,
            EventID._trigger_auto_guild_start_join,
            self
        )

    @async_util.except_return
    async def initialize(self, parent: Any, event_ctrl: EventController):
        """
        Initializes the object.
        """
        self._event_ctrl = event_ctrl
        self.parent = parent
        if self.auto_join is not None:
            if (res := await self.auto_join.initialize(self)) is not None:
                raise res

            self.guild_query_iter = self.auto_join._query_request()

        if self._remove_after is not None:
            if isinstance(self._remove_after, timedelta):
                self._remove_after = datetime.now().astimezone() + self._remove_after
            else:
                self._remove_after = self._remove_after.astimezone()

            self._removal_timer_handle = (
                async_util.call_at(
                    event_ctrl.emit,
                    self._remove_after,
                    EventID._trigger_server_remove,
                    self
                )
            )

        if len(self._invite_join_count):  # Skip invite query from Discord
            try:
                invites = await self._get_invites()
                invites = {invite.id: invite.uses for invite in invites}
                counts = self._invite_join_count
                for invite in list(counts.keys()):
                    try:
                        counts[invite] = invites[invite]
                    except KeyError:
                        del counts[invite]
                        trace(
                            f"Invite link {invite} not found in {self}. It will not be tracked!",
                            TraceLEVELS.ERROR
                        )

                self._event_ctrl.add_listener(
                    EventID.discord_member_join,
                    self._on_member_join,
                    predicate=lambda memb: self.include_pattern.check(memb.guild.name.lower())
                )
                self._event_ctrl.add_listener(
                    EventID.discord_invite_delete,
                    self._on_invite_delete,
                    predicate=lambda inv: self.include_pattern.check(inv.guild.name.lower())
                )
            except discord.HTTPException as exc:
                trace(f"Could not query invite links in {self}", TraceLEVELS.ERROR, exc)

        if self.auto_join is not None:
            self._reset_auto_join_timer()
            event_ctrl.add_listener(EventID._trigger_auto_guild_start_join, self._join_guilds, lambda ag: ag is self)

        self._event_ctrl.add_listener(
            EventID.discord_guild_join,
            self._on_guild_join,
            predicate=lambda guild: self.include_pattern.check(guild.name.lower())
        )

        self._event_ctrl.add_listener(
            EventID.discord_guild_remove,
            self._on_guild_remove,
        )

        event_ctrl.add_listener(EventID._trigger_server_update, self._on_update, lambda server, *args, **kwargs: server is self)

        self._event_ctrl.add_listener(
            EventID.message_removed,
            self._on_message_removed,
            lambda g, m: m in self._messages
        )

        for guild in self._get_guilds():
            await self._make_new_guild(guild)

    def _generate_guild_log_context(self, guild: discord.Guild):
        return {
                "name": guild.name,
                "id": guild.id,
                "type": "GUILD"
        }

    def _generate_invite_log_context(self, member: discord.Member, invite_id: str) -> dict:
        return {
            "id": invite_id,
            "member": {
                "id": member.id,
                "name": member.name
            }
        }

    def _filter_message_context(self, guild: discord.Guild, message_ctx: dict) -> Dict:
        message_ctx = message_ctx.copy()
        message_ctx["channels"] = message_ctx["channels"].copy()

        channel_ctx = message_ctx["channels"]
        guild_channels = set(x.id for x in guild.channels)
        channel_ctx["successful"] = [x for x in channel_ctx["successful"] if x["id"] in guild_channels]
        channel_ctx["failed"] = [x for x in channel_ctx["failed"] if x["id"] in guild_channels]

        return message_ctx if channel_ctx["successful"] or channel_ctx["failed"] else None

    async def _make_new_guild(self, guild: discord.Guild):
        new_guild = GUILD(guild, [d.duplicate() for d in self._messages], self.logging, removal_buffer_length=0)
        if (await new_guild.initialize(self.parent, self._event_ctrl)) is not None:  # not None == exc returned
            return

        self._cache.append(new_guild)

    async def _get_invites(self) -> List[discord.Invite]:
        client: discord.Client = self.parent.client
        invites = []
        for guild in self._get_guilds():
            try:
                perms = guild.get_member(client.user.id).guild_permissions
                if perms.manage_guild:
                    invites.extend(await guild.invites())
            except discord.HTTPException as exc:
                trace(f"Error reading invite links for guild {guild.name}!", TraceLEVELS.ERROR, exc)

        return invites        

    async def _on_update(self, _, init_options, **kwargs):
        await self._close()
        try:
            # Update the guild
            if "invite_track" not in kwargs:
                kwargs["invite_track"] = self.invite_track

            if "exclude_pattern" not in kwargs: # DEPRECATED; TODO: remove in 4.2.0
                kwargs["exclude_pattern"] = None

            kwargs["messages"] = kwargs.pop("messages", self._messages)
            if init_options is None:
                init_options = {"parent": self.parent, "event_ctrl": self._event_ctrl}

            await async_util.update_obj_param(self, init_options=init_options, **kwargs)
        except Exception:
            await self.initialize(self.parent, self._event_ctrl)
            raise

    def _on_message_removed(self, guild: GUILD, message: BaseChannelMessage):
        for duplicator in self._messages:
            if duplicator.message == message:
                duplicator.deduplicate()

        if duplicator.pending_removal:
            self._messages.remove(duplicator)

    @async_util.with_semaphore("update_semaphore")
    async def _join_guilds(self, _):
        """
        Coroutine that joins new guilds thru the web layer.
        """
        # Join Guilds
        discovery = self.auto_join
        selenium: web.SeleniumCLIENT = self.parent.selenium
        client: discord.Client = self.parent.client
        if (
            self.guild_query_iter is None or  # No auto_join provided or iterated though all guilds
            self.guild_join_count == discovery.limit or
            len(client.guilds) == GUILD_MAX_AMOUNT
        ):
            return

        async def get_next_guild():
            try:
                # Get next result from top.gg
                yielded: web.QueryResult = await self.guild_query_iter.__anext__()
                if self.include_pattern.check(yielded.name.lower()):
                    return yielded
            except StopAsyncIteration:
                trace(f"Iterated though all found guilds -> stopping guild join in {self}.", TraceLEVELS.NORMAL)
                self.guild_query_iter = None
            except Exception as exc:
                trace(f"Could not query top.gg, stopping auto join.", TraceLEVELS.ERROR, exc)
                self.guild_query_iter = None

            return None

        while True:
            if (yielded := await get_next_guild()) is None:
                return

            if client.get_guild(yielded.id) is not None:
                self.guild_join_count += 1  # Guilds we are already joined also count
                continue

            try:
                invite_url = await selenium.fetch_invite_link(yielded.url)
                if invite_url is None:
                    raise RuntimeError("Fetching invite link failed")

                await selenium.random_server_click()
                await selenium.join_guild(invite_url)
                await asyncio.sleep(1)
                if client.get_guild(yielded.id) is None:
                    raise RuntimeError(
                        "No error detected in browser,"
                        "but the guild can not be seen by the API wrapper."
                    )
                
                self.guild_join_count += 1  # Increase only on success
            except Exception as exc:
                trace(
                    f"Joining guild raised an error. (Guild '{yielded.name}')",
                    TraceLEVELS.ERROR,
                    exc
                )

            break

        self._reset_auto_join_timer()

    async def _on_member_join(self, member: discord.Member):        
        counts = self._invite_join_count
        invites = await self._get_invites()
        invites = {invite.id: invite.uses for invite in invites}
        for id_, last_uses in counts.items():
            uses = invites[id_]
            if last_uses != uses:
                trace(f"User {member.name} joined to {member.guild.name} with invite {id_}", TraceLEVELS.DEBUG)
                counts[id_] = uses
                invite_ctx = self._generate_invite_log_context(member, id_)
                await logging.save_log(self._generate_guild_log_context(member.guild), None, None, invite_ctx)
                return

    async def _on_invite_delete(self, invite: discord.Invite):
        if invite.id in self._invite_join_count:
            del self._invite_join_count[invite.id]
            guild = invite.guild
            trace(
                f"Invite link ID {invite.id} deleted from {guild.name} (ID: {guild.id} - {self})",
                TraceLEVELS.DEBUG
            )

    async def _on_guild_join(self, guild: discord.Guild):
        await self._make_new_guild(guild)

    async def _on_guild_remove(self, guild: discord.Guild):
        for g in self._cache:
            if g.apiobject == guild:
                await g._close()
                self._cache.remove(g)
                break

    @async_util.with_semaphore("update_semaphore")
    async def _close(self):
        """
        Closes any lower-level async objects.
        """
        if self._event_ctrl is None:  # Not initialized or already closed
            return

        self._event_ctrl.remove_listener(EventID._trigger_auto_guild_start_join, self._join_guilds)
        self._event_ctrl.remove_listener(EventID._trigger_server_update, self._on_update)

        # Remove PyCord API wrapper event handlers.
        self._event_ctrl.remove_listener(EventID.discord_member_join, self._on_member_join)
        self._event_ctrl.remove_listener(EventID.discord_invite_delete, self._on_invite_delete)

        # Remove cleanup events
        self._event_ctrl.remove_listener(EventID.message_removed, self._on_message_removed)

        if self._removal_timer_handle is not None and not self._removal_timer_handle.cancelled():
            self._removal_timer_handle.cancel()
            await asyncio.gather(self._removal_timer_handle, return_exceptions=True)
        
        if self._guild_join_timer_handle is not None and not self._guild_join_timer_handle.cancelled():
            self._guild_join_timer_handle.cancel()
            await asyncio.gather(self._guild_join_timer_handle, return_exceptions=True)

        if self.auto_join is not None:
            await self.auto_join._close()

        for guild in self._cache:
            await guild._close()
        
        self._cache.clear()
