"""
Automatic GUILD generation.
"""
from contextlib import suppress
from copy import deepcopy
from typing import Any, Union, List, Optional, Dict
from typeguard import typechecked
from datetime import timedelta, datetime
from itertools import chain

from ..message import TextMESSAGE, VoiceMESSAGE, BaseMESSAGE
from ..logging.tracing import TraceLEVELS, trace
from ..misc import async_util, instance_track, doc, attributes
from ..events import *

from .guilduser import GUILD

import _discord as discord
import asyncio

from .. import web
from .. import logging

import re


GUILD_JOIN_INTERVAL = timedelta(seconds=45)
GUILD_MAX_AMOUNT = 100

@instance_track.track_id
@doc.doc_category("Auto objects", path="guild")
class AutoGUILD:
    """
    .. versionchanged:: v2.7
        ``interval`` parameter changed to 1 minute.

    Internally automatically creates :class:`daf.guild.GUILD` objects.
    Can also automatically join new guilds (``auto_join`` parameter)

    TODO: Re-design to work like GUILD / USER.

    .. CAUTION::
        Any objects passed to AutoGUILD get **deep-copied** meaning,
        those same objects **will not be initialized** and
        cannot be used to obtain/change information regarding AutoGUILD.

        .. code-block::
            :caption: Illegal use of AutoGUILD
            :emphasize-lines: 6, 7

            auto_ch = daf.AutoCHANNEL(...)
            tm = daf.TextMESSAGE(..., channels=auto_ch)

            await daf.add_object(AutoGUILD(..., messages=[tm]))

            auto_ch.channels # Illegal results in exception
            await tm.update(...) # Illegal results in exception

        To actually modify message/channel objects inside AutoGUILD,
        you need to iterate thru each GUILD.

        .. code-block::
            :caption: Modifying AutoGUILD messages

            aguild = daf.AutoGUILD(..., messages=[tm])
            await daf.add_object(aguild)

            for guild in aguild.guilds:
                for message in guild.messages
                    await message.update(...)

    Parameters
    --------------
    include_pattern: str
        Regex pattern to use for searching guild names that are to be included.
        This is also checked before joining a new guild if ``auto_guild`` is given.

        For example you can do write ``.*`` to match ALL guilds you are joined into or specify
        (parts of) guild names separated with ``|`` like so: "name1|name2|name3|name4"

    exclude_pattern: Optional[str] = None
        Regex pattern to use for searching guild names that are
        **NOT** to be excluded.

        .. note::
            If both include_pattern and exclude_pattern yield a match,
            the guild will be excluded from match.

    remove_after: Optional[Union[timedelta, datetime]] = None
        When to remove this object from the shilling list.
    logging: Optional[bool] = False
        Set to True if you want the guilds generated to log
        sent messages.
    interval: Optional[timedelta] = timedelta(minutes=1)
        Interval at which to scan for new guilds.
    auto_join: Optional[web.GuildDISCOVERY] = None
        .. versionadded:: v2.5

        Optional :class:`~daf.web.GuildDISCOVERY` object which will automatically discover
        and join guilds though the browser.
        This will open a Google Chrome session.
    """
    __slots__ = (
        "include_pattern",
        "exclude_pattern",
        "remove_after",
        "_messages_uninitialized",
        "logging",
        "_created_at",
        "_deleted",
        "update_semaphore",
        "parent",
        "auto_join",
        "guild_query_iter",
        "guild_join_count",
        "invite_track",
        "_messages",
        "_removed_messages",
        "removal_buffer_length",
        "_opened",
    )

    @typechecked
    def __init__(
        self,
        include_pattern: str,
        exclude_pattern: Optional[str] = None,
        remove_after: Optional[Union[timedelta, datetime]] = None,
        messages: Optional[List[Union[TextMESSAGE, VoiceMESSAGE]]] = None,
        logging: Optional[bool] = False,
        auto_join: Optional[web.GuildDISCOVERY] = None,
        invite_track: Optional[List[str]] = None,
        removal_buffer_length: int = 50
    ) -> None:
        # Remove spaces around OR
        self.include_pattern = re.sub(r"\s*\|\s*", '|', include_pattern) if include_pattern else None
        self.exclude_pattern = re.sub(r"\s*\|\s*", '|', exclude_pattern) if exclude_pattern else None
        self.remove_after = remove_after
        self.invite_track = invite_track
        # Uninitialized template messages that get copied for each found guild.
        self._messages_uninitialized = messages if messages is not None else []
        self.logging = logging
        self.auto_join = auto_join
        self._deleted = False
        self._created_at = datetime.now()
        self.parent = None
        self.guild_query_iter = None
        self.guild_join_count = 0
        self._messages: List[BaseMESSAGE] = []
        self._removed_messages: List[BaseMESSAGE] = []
        self.removal_buffer_length = removal_buffer_length
        self._opened = False
        attributes.write_non_exist(self, "update_semaphore", asyncio.Semaphore(1))

    @property
    def created_at(self) -> datetime:
        """
        Returns the datetime of when the object has been created.
        """
        return self._created_at

    @property
    def deleted(self) -> bool:
        """
        Indicates the status of deletion.

        Returns
        -----------
        True
            The object is no longer in the framework and should no longer
            be used.
        False
            Object is in the framework in normal operation.
        """
        return self._deleted

    def _delete(self):
        """
        Sets the internal _deleted flag to True
        and cancels main task.
        """
        self._deleted = True

    def _check_state(self) -> bool:
        """
        Checks if the object is ready to be deleted.

        If the object has already been deleted, return False
        to prevent multiple tasks from trying to remove it multiple
        times which would result in ValueError exceptions.

        Returns
        ----------
        True
            The object should be deleted.
        False
            The object is in proper state, do not delete.
        """
        rm_after_type = type(self.remove_after)
        now = datetime.now()
        return (
            rm_after_type is timedelta and now - self._created_at >
            self.remove_after or
            rm_after_type is datetime and now > self.remove_after)

    async def initialize(self, parent: Any):
        """
        Initializes the object.

        Raises
        --------
        ValueError
            Auto-join guild functionality requires the account to be
            provided with username and password.
        """
        self.parent = parent
        if self.auto_join is not None:
            await self.auto_join.initialize(self)
            self.guild_query_iter = self.auto_join._query_request()

        for message in self._messages_uninitialized:
            try:
                await self.add_message(message)
            except (TypeError, ValueError) as exc:
                trace(f" Unable to initialize message {message}, in {self}", TraceLEVELS.WARNING, exc)
        
        add_listener(EventID.message_ready, self._advertise, lambda m: m.parent is self)
        self._opened = True

    @async_util.with_semaphore("update_semaphore", 1)
    @typechecked
    async def add_message(self, message: BaseMESSAGE):
        """
        Adds a message to the message list.

        .. warning::
            To use this method, the guild must already be added to the
            framework's shilling list (or initialized).

        Parameters
        --------------
        message: BaseMESSAGE
            Message object to add.

        Raises
        --------------
        TypeError
            Raised when the message is not of type the guild allows.
        Other
            Raised from message.initialize() method.
        """
        await message.initialize(parent=self, allowed_channels=set(chain(*(g.channels for g in self.guilds))))
        self._messages.append(message)
        with suppress(ValueError):  # Readd the removed message
            self._removed_messages.remove(message)

    @async_util.with_semaphore("update_semaphore", 1)
    @typechecked
    async def remove_message(self, message: BaseMESSAGE):
        """
        Removes a message from the message list.

        .. versionchanged:: 2.11

            The function is now async.

        Parameters
        --------------
        message: BaseMESSAGE
            Message object to remove.

        Raises
        --------------
        TypeError
            Raised when the message is not of type the guild allows.
        ValueError
            Raised when the message is not present in the list.
        """
        trace(f"Removing message {message} from {self}", TraceLEVELS.NORMAL)
        message._delete()
        await message._close()
        self._messages.remove(message)
        self._removed_messages.append(message)
        if len(self._removed_messages) > self.removal_buffer_length:
            trace(f"Removing oldest record of removed messages {self._removed_messages[0]}", TraceLEVELS.DEBUG)
            del self._removed_messages[0]

    async def _join_guilds(self):
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
            datetime.now() - self.last_guild_join < GUILD_JOIN_INTERVAL or
            len(client.guilds) == GUILD_MAX_AMOUNT
        ):
            return

        async def get_next_guild():
            try:
                # Get next result from top.gg
                yielded: web.QueryResult = await self.guild_query_iter.__anext__()
                if (
                    re.search(self.include_pattern, yielded.name) is None or
                    (
                        self.exclude_pattern is not None and
                        re.search(self.exclude_pattern, yielded.name) is not None
                    )
                ):
                    return None

                return yielded
            except StopAsyncIteration:
                trace(f"Iterated though all found guilds -> stopping guild join in {self}.", TraceLEVELS.NORMAL)
                self.guild_query_iter = None

        if (yielded := await get_next_guild()) is None:
            return

        no_error = True
        # Not already joined in the guild
        if client.get_guild(yielded.id) is None:
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
            except Exception as exc:
                no_error = False
                trace(
                    f"Joining guild raised an error. (Guild '{yielded.name}')",
                    TraceLEVELS.ERROR,
                    exc
                )

            self.last_guild_join = datetime.now()

        if no_error:
            # Don't count errored joins but count guilds we are already joined if they match the pattern
            self.guild_join_count += 1

    @async_util.with_semaphore("update_semaphore")
    async def _close(self):
        """
        Closes any lower-level async objects.
        """
        remove_listener(EventID.message_ready, self._advertise)
        self._opened = False
        if self.auto_join is not None:
            await self.auto_join._close()

        for message in self._messages:
            await message._close()

    @property
    def guilds(self) -> List[discord.Guild]:
        "Returns all the guilds that match the include_pattern and not exclude_pattern"
        client: discord.Client = self.parent.client
        return [
            g for g in client.guilds
            if re.search(self.include_pattern, g.name) is not None and
               (self.exclude_pattern is None or re.search(self.exclude_pattern, g.name) is None)
        ]

    def _generate_guild_log_context(self, guild: discord.Guild):
        return {
                "name": guild.name,
                "id": guild.id,
                "type": GUILD
        }

    def _filter_message_context(self, guild: discord.Guild, message_ctx: dict) -> Dict:
        message_ctx = message_ctx.copy()
        channel_ctx = message_ctx["channels"]
        guild_channels = set(x.id for x in guild.channels)
        channel_ctx["successful"] = [x for x in channel_ctx["successful"] if x["id"] in guild_channels]
        channel_ctx["failed"] = [x for x in channel_ctx["failed"] if x["id"] in guild_channels]

        return message_ctx if channel_ctx["successful"] or channel_ctx["failed"] else None

    @async_util.with_semaphore("update_semaphore", 1)
    async def _advertise(self, message: BaseMESSAGE):
        """
        Advertises thru all the GUILDs.
        """
        if message._check_state():
            await self.remove_message(message)
            return
        
        author_ctx = self.parent.generate_log_context()
        message_context = await message._send()
        if message_context and self.logging:
            for guild in self.guilds:
                guild_ctx = self._generate_guild_log_context(guild)
                message_guild_ctx = self._filter_message_context(guild, message_context)
                if message_guild_ctx:
                    await logging.save_log(guild_ctx, message_guild_ctx, author_ctx)

        # Must be called after ._send to prevent multiple _advertise calls being added to
        # the event loop queue in case the period is lower than the time it takes to send the message.
        if self._opened:  # In case the event loop called _advertise during after / during _close request
            message._reset_timer()

    async def update(self, init_options = None, **kwargs):
        """
        Updates the object with new initialization parameters.

        .. WARNING::
            After calling this method the entire object is reset
            (this includes it's GUILD objects in cache).
        """
        if init_options is None:
            init_options = {"parent": self.parent}

        await self._close()
        try:
            return await async_util.update_obj_param(self, init_options=init_options, **kwargs)
        finally:        
            if self.parent is not None:  # Only if it were previously initialized
                await self.initialize(self.parent)  # Reopen any async related connections
