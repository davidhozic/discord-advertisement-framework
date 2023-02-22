"""
    This module contains the class definitions for all things
    regarding the guild and also defines a USER class from the
    _BaseGUILD class.
"""
from typing import Any, Coroutine, Union, List, Optional, Dict, Callable, Set
from typeguard import typechecked
from datetime import timedelta, datetime
from copy import deepcopy

from .logging.tracing import TraceLEVELS, trace
from .message import *

from . import logging
from . import misc
from . import web

import _discord as discord
import asyncio
import re


__all__ = (
    "GUILD",
    "USER",
    "AutoGUILD",
)


GUILD_ADVERT_STATUS_SUCCESS = 0
GUILD_ADVERT_STATUS_ERROR_REMOVE_ACCOUNT = None

GUILD_JOIN_INTERVAL = timedelta(seconds=15)
GUILD_MAX_AMOUNT = 100

globals_ = globals()
prev_val = 0
for k, v in globals_.copy().items():
    if k.startswith("GUILD_ADVERT_"):
        if isinstance(v, int):
            prev_val = v
        else:
            prev_val += 1
            globals_[k] = prev_val


class _BaseGUILD:
    """
    Represents an universal guild.

    .. versionchanged:: v2.1

        - Added ``created_at`` attribute
        - Added ``remove_after`` parameter


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
    """

    __slots__ = (       # Faster attribute access
        "_apiobject",
        "logging",
        "_messages_uninitialized",
        "_messages",
        "remove_after",
        "_created_at",
        "_deleted",
        "parent"
    )

    def __init__(
        self,
        snowflake: Any,
        messages: Optional[List] = [],
        logging: Optional[bool] = False,
        remove_after: Optional[Union[timedelta, datetime]] = None
    ) -> None:
        self._apiobject: discord.Object = snowflake
        self.logging: bool = logging
        # Contains all the different message objects (added in .initialize())
        self._messages_uninitialized: list = messages
        self._messages: List[BaseMESSAGE] = []
        self.remove_after = remove_after
        # int - after n sends
        # timedelta - after amount of time
        # datetime - after that time

        self._deleted = False
        self._created_at = datetime.now()  # The time this object was created
        self.parent = None

    def __repr__(self) -> str:
        return f"{type(self).__name__}(discord={self._apiobject})"

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
    def created_at(self) -> datetime:
        """
        .. versionadded:: v2.1

        Returns the datetime of when the object has been created.
        """
        return self._created_at

    def _check_state(self) -> bool:
        """
        Checks if the guild is ready to be deleted.

        Returns
        ----------
        True
            The guild should be deleted.
        False
            The guild is in proper state, do not delete.
        """
        type_ = type(self.remove_after)
        dt = datetime.now()
        return (
            self.deleted or  # Force delete
            type_ is timedelta and dt - self._created_at > self.remove_after or
            type_ is datetime and dt > self.remove_after
        )

    def __eq__(self, other: Any) -> bool:
        """
        Compares two guild objects if they're equal.
        """
        return self.snowflake == other.snowflake

    def _delete(self):
        """
        Sets the internal _deleted flag to True.
        """
        self._deleted = True
        for message in self._messages:
            message._delete()

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
        await message.initialize(parent=self)
        self._messages.append(message)

    @typechecked
    def remove_message(self, message: BaseMESSAGE):
        """
        Removes a message from the message list.

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
        message._delete()
        self._messages.remove(message)

    async def initialize(self, parent: Any, getter: Callable) -> None:
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

        Raises
        -----------
        ValueError
            Raised when the guild_id wasn't found.
        Other
            Raised from .add_message(message_object) method.
        """
        self.parent = parent
        guild_id = self.snowflake
        if isinstance(self._apiobject, int):
            self._apiobject = getter(guild_id)
            if isinstance(self._apiobject, Coroutine):
                self._apiobject = await self._apiobject

        if self._apiobject is not None:
            for message in self._messages_uninitialized:
                try:
                    await self.add_message(message)
                except (TypeError, ValueError) as exc:
                    trace(f" Unable to initialize message {message}, in {self}", TraceLEVELS.WARNING, exc)

            self._messages_uninitialized.clear()
            return

        raise ValueError(f"Unable to find object with ID: {guild_id}")

    async def update(self, init_options={}, **kwargs):
        """
        .. versionadded:: v2.0

        Used for changing the initialization parameters,
        the object was initialized with.

        .. warning::
            This method will BLOCK until every message has finished shilling!
            This is done for safety due to asynchronous operations.

        .. warning::
            Upon updating, the internal state of objects get's reset,
            meaning you basically have a brand new created object.

        Parameters
        -------------
        **kwargs: Any
            Custom number of keyword parameters which you want to update,
            these can be anything that is available during the object creation.
        """
        raise NotImplementedError

    @misc._async_safe("update_semaphore", 1)
    async def _advertise(self) -> int:
        """
        Common to all messages, function responsible for sending all the
        messages to this specific guild.

        Returns
        -----------
        int
            Enumerated advertisement result.
        """
        to_advert: List[BaseMESSAGE] = []
        to_remove: List[BaseMESSAGE] = []
        guild_ctx = self.generate_log_context()

        for message in self._messages:
            if message._check_state():
                to_remove.append(message)

            elif message._is_ready():
                to_advert.append(message)

        # Remove prior to awaits to prevent any user tasks
        # from removing the message causing ValueErrors
        for message in to_remove:
            self.remove_message(message)

        # Await coroutines outside the main loop to prevent list modification
        # while iterating, this way even if the user removes the message,
        # it will still be shilled but no exceptions will be raised when
        # trying to remove the message.
        for message in to_advert:
            result: MessageSendResult = await message._send()
            message._reset_timer()
            if self.logging and result.result_code != MSG_SEND_STATUS_NO_MESSAGE_SENT:
                await logging.save_log(guild_ctx, result.message_context)

            if result.result_code == MSG_SEND_STATUS_ERROR_REMOVE_GUILD:
                # Will be removed by ACCOUNT at next advertisement attempt
                self._delete()
                break

            elif result.result_code == MSG_SEND_STATUS_ERROR_REMOVE_ACCOUNT:
                return GUILD_ADVERT_STATUS_ERROR_REMOVE_ACCOUNT

        return GUILD_ADVERT_STATUS_SUCCESS

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


@misc.doc_category("Guilds")
@logging.sql.register_type("GuildTYPE")
class GUILD(_BaseGUILD):
    """
    The GUILD object represents a server to which messages will be sent.

    .. versionchanged:: v2.1

        - Added ``created_at`` attribute
        - Added ``remove_after`` parameter

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
    """
    __slots__ = (
        "update_semaphore",
    )

    @typechecked
    def __init__(self,
                 snowflake: Union[int, discord.Guild],
                 messages: Optional[List[Union[TextMESSAGE, VoiceMESSAGE]]] = [],
                 logging: Optional[bool] = False,
                 remove_after: Optional[Union[timedelta, datetime]] = None):
        super().__init__(snowflake, messages, logging, remove_after)
        misc._write_attr_once(self, "update_semaphore", asyncio.Semaphore(1))

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
        return (self.parent.client.get_guild(self.snowflake) is None or
                super()._check_state())

    async def initialize(self, parent: Any) -> None:
        """
        This function initializes the API related objects and
        then tries to initialize the MESSAGE objects.

        .. note::
            This should NOT be manually called, it is called automatically
            after adding the message.

        Raises
        -----------
        ValueError
            Raised when the guild_id wasn't found.
        Other
            Raised from .add_message(message_object) method.
        """
        return await super().initialize(parent, parent.client.get_guild)

    @misc._async_safe("update_semaphore", 1)
    async def update(self, init_options={}, **kwargs):
        """
        Used for changing the initialization parameters,
        the object was initialized with.

        .. versionadded:: v2.0

        .. warning::
            Upon updating, the internal state of objects get's reset,
            meaning you basically have a brand new created object.
            It also resets the message objects.

        Parameters
        -------------
        **kwargs: Any
            Custom number of keyword parameters which you want to update,
            these can be anything that is available during the object creation.

        Raises
        -----------
        TypeError
            Invalid keyword argument was passed.
        Other
            Raised from .initialize() method.
        """
        # Update the guild
        if "snowflake" not in kwargs:
            kwargs["snowflake"] = self.snowflake

        if len(init_options) == 0:
            init_options = {"parent": self.parent}

        await misc._update(self, **kwargs, init_options=init_options)
        # Update messages
        for message in self.messages:
            await message.update(_init_options={"parent": self})


@misc.doc_category("Guilds")
@logging.sql.register_type("GuildTYPE")
class USER(_BaseGUILD):
    """
    The USER object represents a user to whom messages will be sent.

    .. versionchanged:: v2.1

        - Added ``created_at`` attribute
        - Added ``remove_after`` parameter

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
    """
    __slots__ = (
        "update_semaphore",
    )

    @typechecked
    def __init__(
        self,
        snowflake: Union[int, discord.User],
        messages: Optional[List[DirectMESSAGE]] = [],
        logging: Optional[bool] = False,
        remove_after: Optional[Union[timedelta, datetime]] = None
    ) -> None:
        super().__init__(snowflake, messages, logging, remove_after)
        misc._write_attr_once(self, "update_semaphore", asyncio.Semaphore(1))

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

    async def initialize(self, parent: Any):
        """
        This function initializes the API related objects and
        then tries to initialize the MESSAGE objects.

        Raises
        -----------
        ValueError
            Raised when the DM could not be created.
        Other
            Raised from .add_message(message_object) method.
        """
        return await super().initialize(
            parent,
            parent.client.get_or_fetch_user
        )

    @misc._async_safe("update_semaphore", 1)
    async def update(self, init_options={}, **kwargs):
        """
        .. versionadded:: v2.0

        Used for changing the initialization parameters,
        the object was initialized with.

        .. warning::
            Upon updating, the internal state of objects get's reset,
            meaning you basically have a brand new created object.
            It also resets the message objects.

        Parameters
        -------------
        **kwargs: Any
            Custom number of keyword parameters which you want to update,
            these can be anything that is available during the object creation.

        Raises
        -----------
        TypeError
            Invalid keyword argument was passed.
        Other
            Raised from .initialize() method.
        """
        # Update the guild
        if "snowflake" not in kwargs:
            kwargs["snowflake"] = self.snowflake

        if len(init_options) == 0:
            init_options = {"parent": self.parent}

        await misc._update(self, init_options=init_options, **kwargs)

        # Update messages
        for message in self.messages:
            await message.update(_init_options={"parent": self})


@misc.doc_category("Auto objects")
class AutoGUILD:
    """
    .. versionchanged:: v2.5
        Added ``auto_join`` parameter.

    Internally automatically creates :class:`daf.guild.GUILD` objects.
    Can also automatically join new guilds (``auto_join`` parameter)

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
    interval: Optional[timedelta] = timedelta(minutes=10)
        Interval at which to scan for new guilds
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
        "join_history",
        "guild_query_iter",
        "last_guild_join",
        "guild_join_count"
    )

    @typechecked
    def __init__(self,
                 include_pattern: str,
                 exclude_pattern: Optional[str] = None,
                 remove_after: Optional[Union[timedelta, datetime]] = None,
                 messages: Optional[List[BaseMESSAGE]] = [],
                 logging: Optional[bool] = False,
                 interval: Optional[timedelta] = timedelta(minutes=10),
                 auto_join: Optional[web.GuildDISCOVERY] = None) -> None:
        self.include_pattern = include_pattern
        self.exclude_pattern = exclude_pattern
        self.remove_after = remove_after
        # Uninitialized template messages that get copied for each found guild.
        self.messages = messages
        self.logging = logging
        self.interval = interval
        self.auto_join = auto_join
        self.cache: Dict[discord.Guild, GUILD] = {}
        self.join_history: Set[int] = set()  # History of auto-joined guild ids
        self.last_scan = datetime.min
        self._deleted = False
        self._created_at = datetime.now()
        self.parent = None
        self.guild_query_iter = None
        self.last_guild_join = datetime.min
        self.guild_join_count = 0
        misc._write_attr_once(self, "_safe_sem", asyncio.Semaphore(2))

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

    async def add_message(self, message: BaseMESSAGE):
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
            await guild.add_message(deepcopy(message))

    def remove_message(self, message: BaseMESSAGE):
        """
        Removes message from the messages list.

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
            guild.remove_message(message)

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
                discord_guild not in self.cache and
                re.search(self.include_pattern, discord_guild.name) is not None and
                (
                    self.exclude_pattern is None or
                    re.search(self.exclude_pattern, discord_guild.name) is None
                )
            ):
                try:
                    new_guild = GUILD(snowflake=discord_guild,
                                      messages=deepcopy(self.messages),
                                      logging=self.logging)

                    await new_guild.initialize(parent=self.parent)
                    self.cache[discord_guild] = new_guild
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
            discovery is None or  # No auto_join provided
            self.guild_join_count == discovery.limit or
            datetime.now() - self.last_guild_join < GUILD_JOIN_INTERVAL or
            len(client.guilds) == GUILD_MAX_AMOUNT
        ):
            return

        try:
            # Get next result from top.gg
            yielded: web.QueryResult = await anext(self.guild_query_iter)
            if (
                re.search(self.include_pattern, yielded.name) is None or
                (
                    self.exclude_pattern is not None and
                    re.search(self.exclude_pattern, yielded.name) is not None
                )
            ):
                return

            # Not already joined in the guild
            try:
                if client.get_guild(yielded.id) is None:
                    await selenium.random_server_click()
                    await selenium.join_guild(yielded.invite)
                    await asyncio.sleep(1)
                    if client.get_guild(yielded.id) is None:
                        raise RuntimeError(
                            "No error detected in browser,"
                            "but the guild can not be seen by the API wrapper."
                        )
            except Exception as exc:
                trace(
                    f"Joining guild raised an error. (Guild '{yielded.name}')",
                    TraceLEVELS.ERROR,
                    exc
                )
            else:
                # Increase the join count if there was no exception (what 'else' does after a try clause),
                # regardless if the user was already inside the guild or not.
                self.guild_join_count += 1
                self.last_guild_join = datetime.now()

        except StopAsyncIteration:
            self.guild_query_iter = discovery._query_request()

    @misc._async_safe("_safe_sem", 1)
    async def _advertise(self):
        """
        Advertises thru all the GUILDs.
        """
        await self._generate_guilds()
        await self._join_guilds()
        for g in self.guilds:
            if g._check_state():
                del self.cache[g.apiobject]
            else:
                status = await g._advertise()
                if status == GUILD_ADVERT_STATUS_ERROR_REMOVE_ACCOUNT:
                    return GUILD_ADVERT_STATUS_ERROR_REMOVE_ACCOUNT

        return GUILD_ADVERT_STATUS_SUCCESS

    @misc._async_safe("_safe_sem", 1)
    async def update(self, init_options={}, **kwargs):
        """
        Updates the object with new initialization parameters.

        .. WARNING::
            After calling this method the entire object is reset
            (this includes it's GUILD objects in cache).
        """
        if len(init_options) == 0:
            init_options = {"parent": self.parent}

        await self._close()
        return await misc._update(self, init_options=init_options, **kwargs)
