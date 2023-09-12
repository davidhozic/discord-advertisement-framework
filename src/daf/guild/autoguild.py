"""
Automatic GUILD generation.
"""
from contextlib import suppress
from copy import deepcopy
from typing import Any, Union, List, Optional, Dict
from typeguard import typechecked
from datetime import timedelta, datetime

from ..message import TextMESSAGE, VoiceMESSAGE, BaseMESSAGE
from ..logging.tracing import TraceLEVELS, trace
from ..misc import async_util, instance_track, doc, attributes

from .guilduser import GUILD

import _discord as discord
import asyncio

from .. import web

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
        "messages",
        "logging",
        "interval",
        "cache",
        "last_scan",
        "_created_at",
        "_deleted",
        "_safe_sem",
        "parent",
        "auto_join",
        "guild_query_iter",
        "last_guild_join",
        "guild_join_count",
        "invite_track",
    )

    @typechecked
    def __init__(self,
                 include_pattern: str,
                 exclude_pattern: Optional[str] = None,
                 remove_after: Optional[Union[timedelta, datetime]] = None,
                 messages: Optional[List[Union[TextMESSAGE, VoiceMESSAGE]]] = None,
                 logging: Optional[bool] = False,
                 interval: Optional[timedelta] = timedelta(minutes=1),
                 auto_join: Optional[web.GuildDISCOVERY] = None,
                 invite_track: Optional[List[str]] = None) -> None:
        # Remove spaces around OR
        self.include_pattern = re.sub(r"\s*\|\s*", '|', include_pattern) if include_pattern else None
        self.exclude_pattern = re.sub(r"\s*\|\s*", '|', exclude_pattern) if exclude_pattern else None
        self.remove_after = remove_after
        self.invite_track = invite_track
        # Uninitialized template messages that get copied for each found guild.
        self.messages = messages if messages is not None else []
        self.logging = logging
        self.interval = interval
        self.auto_join = auto_join
        self.cache: Dict[int, GUILD] = {}
        self.last_scan = datetime.min
        self._deleted = False
        self._created_at = datetime.now()
        self.parent = None
        self.guild_query_iter = None
        self.last_guild_join = datetime.min
        self.guild_join_count = 0
        attributes.write_non_exist(self, "_safe_sem", asyncio.Semaphore(1))

    @property
    def guilds(self) -> List[GUILD]:
        "Returns cached found GUILD objects."
        return list(self.cache.values())

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

    async def _close(self):
        """
        Closes any lower-level async objects.
        """
        if self.auto_join is not None:
            await self.auto_join._close()

    async def add_message(self, message: Union[TextMESSAGE, VoiceMESSAGE]):
        """
        Adds a copy of the passed message to each
        guild inside cache.

        Parameters
        -------------
        message: message.BaseMESSAGE
            Message to add.

        Raises
        ---------
        Any
            Any exception raised in :py:meth:`daf.guild.GUILD.add_message`.
        """
        self.messages.append(message)
        for guild in self.cache.values():
            try:
                await guild.add_message(deepcopy(message))
            except Exception:
                trace(f"Could not add message {message} to {guild}, cached in {self}", TraceLEVELS.WARNING)

    async def remove_message(self, message: BaseMESSAGE):
        """
        Removes message from the messages list.

        .. versionchanged:: v2.11

            Turned async to support event loop.

        Parameters
        ------------
        message: BaseMESSAGE
            The message to remove.

        Raises
        --------
        ValueError
            The message is not present in the list.
        """
        self.messages.remove(message)
        for guild in self.guilds:
            with suppress(ValueError):  # Guilds can remove messages themselves
                await guild.remove_message(message)

    def _get_server(self, snowflake: Union[int, discord.Guild, discord.User, discord.Object]):
        """
        Retrieves the server from internal cache based on the snowflake id or discord API object.

        Parameters
        -------------
        snowflake: Union[int, discord.Guild, discord.User, discord.Object]
            Snowflake ID or Discord API object.

        Returns
        ---------
        Union[guild.GUILD, guild.USER]
            The DAF server object.
        None
            The object was not found.
        """
        if not isinstance(snowflake, int):
            snowflake = snowflake.id

        return self.cache.get(snowflake)

    async def _generate_guilds(self):
        """
        Coroutine generates GUILD object for every joined guild that matches
        the regex pattern of ``include_pattern`` parameter but does not
        """
        stamp = datetime.now()
        if stamp - self.last_scan < self.interval:
            return

        # Create GUILD instances
        client: discord.Client = self.parent.client
        for discord_guild in client.guilds:
            if (
                discord_guild.id not in self.cache and
                discord_guild.name is not None and
                re.search(self.include_pattern, discord_guild.name) is not None and
                (
                    self.exclude_pattern is None or
                    re.search(self.exclude_pattern, discord_guild.name) is None
                )
            ):
                try:
                    new_guild = GUILD(snowflake=discord_guild,
                                      messages=deepcopy(self.messages),
                                      logging=self.logging,
                                      invite_track=self.invite_track)

                    await new_guild.initialize(parent=self.parent)
                    self.cache[discord_guild.id] = new_guild
                except Exception as exc:
                    trace("Unable to add new object.", TraceLEVELS.WARNING, exc)

        self.last_scan = stamp

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

    @async_util.with_semaphore("_safe_sem", 1)
    async def _advertise(self):
        """
        Advertises thru all the GUILDs.
        """
        await self._generate_guilds()
        await self._join_guilds()
        for g in self.guilds:
            if g._check_state():
                del self.cache[g.apiobject.id]
            else:
                await g._advertise()

    @async_util.with_semaphore("_safe_sem", 1)
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
        except Exception:
            self.cache.clear()
            if self.parent is not None:  # Only if it were previously initialized
                await self.initialize(self.parent)  # Reopen any async related connections

            raise
