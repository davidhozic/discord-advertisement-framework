"""
    This module contains the class definitions for all things
    regarding the guild and also defines a USER class from the
    _BaseGUILD class.
"""
from __future__ import annotations

from typing import Any, Coroutine, Union, List, Optional, Dict, Callable
from contextlib import suppress
from typeguard import typechecked
from datetime import timedelta, datetime
from enum import Enum
from copy import deepcopy

from .logging.tracing import *
from .message import *

from . import client
from .logging import sql
from . import misc
from .logging import logging

import _discord as discord
import operator
import asyncio
import re


__all__ = (
    "GUILD",
    "USER",
    "AutoGUILD"
)

class AdvertiseTaskType(Enum):
    """
    Used for identifying advertiser tasks
    """
    TEXT_ISH = 0
    VOICE = 1


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
        "apiobject",
        "logging",
        "_messages_uninitialized",
        "message_dict",
        "remove_after",
        "_created_at",
        "_deleted"
    )
    
    def __init__(self,
                 snowflake: Any,
                 messages: Optional[List]=[],
                 logging: Optional[bool]=False,
                 remove_after: Optional[Union[timedelta, datetime]]=None) -> None:

        self.apiobject: discord.Object = snowflake
        self.logging: bool= logging
        self._messages_uninitialized: list = messages   # Contains all the different message objects, this gets sorted in `.initialize()` method
        self.message_dict: Dict[str, List[BaseMESSAGE]] = {AdvertiseTaskType.TEXT_ISH: [], AdvertiseTaskType.VOICE: []}  # Dictionary, which's keys hold the discord message type(text, voice) and keys are a list of messages
        self.remove_after = remove_after  # int - after n sends; timedelta - after amount of time; datetime - after that time
        self._deleted = False
        self._created_at = datetime.now() # The time this object was created

    def __repr__(self) -> str:
        return f"{type(self).__name__}(discord={self.apiobject})"

    @property
    def messages(self) -> List[BaseMESSAGE]:
        """
        Returns all the (initialized) message objects inside the object.

        .. versionadded:: v2.0
        """
        return operator.add(*self.message_dict.values()) # Merge lists

    @property
    def snowflake(self) -> int:
        """
        .. versionadded:: v2.0

        Returns the discord's snowflake ID.
        """
        return self.apiobject if isinstance(self.apiobject, int) else self.apiobject.id
    
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
        rm_after_type = type(self.remove_after)
        return (rm_after_type is timedelta and datetime.now() - self._created_at > self.remove_after or # The difference from creation time is bigger than remove_after
                rm_after_type is datetime and datetime.now() > self.remove_after) # The current time is larger than remove_after 

    def __eq__(self, other: _BaseGUILD) -> bool:
        """
        Compares two guild objects if they're equal.
        """
        return self.snowflake == other.snowflake

    def _delete(self):
        """
        Sets the internal _deleted flag to True.
        """
        self._deleted = True

    async def add_message(self, message: BaseMESSAGE):
        """
        Adds a message to the message list.

        Parameters
        -----------
        message: BaseMESSAGE
            Message object to add.
        """
        raise NotImplementedError

    async def initialize(self, getter: Callable) -> None:
        """
        This function initializes the API related objects and then tries to initialize the MESSAGE objects.

        .. warning::
            This should NOT be manually called, it is called automatically after adding the message.

        .. versionchanged:: v2.1
            Merged derived classes' methods into base method to reduce code.

        Parameters
        ------------
        getter: Callable
            Callable function or async generator used for retrieving an api object (client.get_*).

        Raises
        -----------
        ValueError
            Raised when the guild_id wasn't found.
        Other
            Raised from .add_message(message_object) method.
        """
        guild_id = self.snowflake
        if isinstance(self.apiobject, int):
            self.apiobject = getter(guild_id)
            if isinstance(self.apiobject, Coroutine):
                self.apiobject = await self.apiobject

        if self.apiobject is not None:
            for message in self._messages_uninitialized:
                try:
                    await self.add_message(message)
                except (TypeError, ValueError) as exc:
                    trace(f"[GUILD:] Unable to initialize message {message}, in {self}\nReason: {exc}", TraceLEVELS.WARNING)


            self._messages_uninitialized.clear()
            return

        raise ValueError(f"Unable to find object with ID: {guild_id}")

    def remove_message(self, message: BaseMESSAGE):
        """
        Removes a message from the message list.

        Parameters
        --------------
        message: message.BaseMESSAGE
            Message object to remove."""
        raise NotImplementedError

    async def update(self, **kwargs):
        """
        .. versionadded:: v2.0

        Used for changing the initialization parameters the object was initialized with.

        .. warning::
            This method will BLOCK until every message has finished shilling!
            This is done for safety due to asynchronous operations.

        .. warning::
            Upon updating, the internal state of objects get's reset, meaning you basically have a brand new created object.

        Parameters
        -------------
        **kwargs: Any
            Custom number of keyword parameters which you want to update, these can be anything that is available during the object creation.
        """
        raise NotImplementedError

    @misc._async_safe("update_semaphore", 1)
    async def _advertise(self,
                         mode: AdvertiseTaskType):
        """
        Main coroutine responsible for sending all the messages to this specific guild,
        it is called from the core module's advertiser task.

        Parameters
        --------------
        mode: AdvertiseTaskType
            Tells which task called this method (there is one task for textual messages and one for voice like messages).
        """
        msg_list = self.message_dict[mode]
        for message in msg_list[:]: # Copy the avoid issues with the list being modified while iterating (add_message/remove_message)
            # Message removal             Check due to asynchronous operations
            if message._check_state():
                # Suppress since user could of called the remove_object function mid iteration.
                with suppress(ValueError):
                    self.remove_message(message)

            elif message._is_ready():
                message._reset_timer()
                message_ret = await message._send()

                # Generate log (JSON or SQL)
                if self.logging and message_ret is not None:
                    await logging.save_log(self.generate_log_context(), message_ret)

    def generate_log_context(self) -> Dict[str, Union[str, int]]:
        """
        Generates a dictionary of the guild's context,
        which is then used for logging.

        Returns
        ---------
        Dict[str, Union[str, int]]
        """
        return {
            "name": self.apiobject.name,
            "id": self.apiobject.id,
            "type": type(self).__name__
        }

@misc.doc_category("Guilds")
@sql.register_type("GuildTYPE")
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
        Optional variable dictating whatever to log sent messages inside this guild.
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
                 messages: Optional[List[Union[TextMESSAGE, VoiceMESSAGE]]]=[],
                 logging: Optional[bool]=False,
                 remove_after: Optional[Union[timedelta, datetime]]=None):
        super().__init__(snowflake, messages, logging, remove_after)
        misc._write_attr_once(self, "update_semaphore", asyncio.Semaphore(2))

    @typechecked
    async def add_message(self, message: Union[TextMESSAGE, VoiceMESSAGE]):
        """
        Adds a message to the message list.

        .. warning::
            To use this method, the guild must already be added to the framework's shilling list (or initialized).

        Parameters
        --------------
        message: Union[TextMESSAGE, VoiceMESSAGE]
            Message object to add.

        Raises
        --------------
        TypeError
            Raised when the message is not of type TextMESSAGE or VoiceMESSAGE.
        Other
            Raised from message.initialize() method.
        """
        await message.initialize(parent=self)
        self.message_dict[AdvertiseTaskType.TEXT_ISH if isinstance(message, TextMESSAGE) else AdvertiseTaskType.VOICE].append(message)

    @typechecked
    def remove_message(self, message: Union[TextMESSAGE, VoiceMESSAGE]):
        """
        Removes a message from the message list.

        Parameters
        --------------
        message: Union[TextMESSAGE, VoiceMESSAGE]
            Message object to remove.

        Raises
        --------------
        TypeError
            Raised when the message is not of type TextMESSAGE or VoiceMESSAGE.
        ValueError
            Raised when the message is not present in the list.
        """
        self.message_dict[AdvertiseTaskType.TEXT_ISH if isinstance(message, TextMESSAGE) else AdvertiseTaskType.VOICE].remove(message)

    async def initialize(self) -> None:
        """
        This function initializes the API related objects and then tries to initialize the MESSAGE objects.

        .. note::
            This should NOT be manually called, it is called automatically after adding the message.

        Raises
        -----------
        ValueError
            Raised when the guild_id wasn't found.

        Other
            Raised from .add_message(message_object) method.
        """
        return await super().initialize(client.get_client().get_guild)
    
    @misc._async_safe("update_semaphore", 2) # Take 2 since 2 tasks share access
    async def update(self, **kwargs):
        """
        Used for changing the initialization parameters the object was initialized with.

        .. versionadded:: v2.0

        .. warning::
            Upon updating, the internal state of objects get's reset, meaning you basically have a brand new created object.
            It also resets the message objects.

        Parameters
        -------------
        **kwargs: Any
            Custom number of keyword parameters which you want to update, these can be anything that is available during the object creation.

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

        await misc._update(self, **kwargs)
        # Update messages
        for message in self.messages:
            await message.update(_init_options={"parent": self})


@misc.doc_category("Guilds")
@sql.register_type("GuildTYPE")
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
        Optional variable dictating whatever to log sent messages inside this guild.
    remove_after: Optional[Union[timedelta, datetime]]
        Deletes the user after:

        * timedelta - the specified time difference
        * datetime - specific date & time
    """
    __slots__ = (
        "update_semaphore",
    )

    @typechecked
    def __init__(self,
                 snowflake: Union[int, discord.User],
                 messages: Optional[List[DirectMESSAGE]]=[],
                 logging: Optional[bool] = False,
                 remove_after: Optional[Union[timedelta, datetime]]=None) -> None:
        super().__init__(snowflake, messages, logging, remove_after)
        misc._write_attr_once(self, "update_semaphore", asyncio.Semaphore(2)) # Only allows re-referencing this attribute once

    @typechecked
    async def add_message(self, message: DirectMESSAGE):
        """
        Adds a message to the message list.

        .. warning::
            To use this method, the guild must already be added to the framework's shilling list (or initialized).

        Parameters
        --------------
        message: DirectMESSAGE
            Message object to add.

        Raises
        --------------
        TypeError
            Raised when the message is not of type DirectMESSAGE.
        Other
            Raised from message.initialize() method.
        """
        await message.initialize(parent=self)
        self.message_dict[AdvertiseTaskType.TEXT_ISH].append(message)

    @typechecked
    def remove_message(self, message: DirectMESSAGE):
        """
        .. versionadded:: v2.0

        Removes a message from the message list.

        Parameters
        --------------
        message: DirectMESSAGE
            Message object to remove.

        Raises
        --------------
        TypeError
            Raised when the message is not of type DirectMESSAGE.
        """
        self.message_dict[AdvertiseTaskType.TEXT_ISH].remove(message)

    async def initialize(self):
        """
        This function initializes the API related objects and then tries to initialize the MESSAGE objects.

        Raises
        -----------
        ValueError
            Raised when the DM could not be created.
        Other
            Raised from .add_message(message_object) method.
        """
        return await super().initialize(client.get_client().get_or_fetch_user)

    @misc._async_safe("update_semaphore", 2)
    async def update(self, **kwargs):
        """
        .. versionadded:: v2.0

        Used for changing the initialization parameters the object was initialized with.

        .. warning::
            Upon updating, the internal state of objects get's reset, meaning you basically have a brand new created object.
            It also resets the message objects.

        Parameters
        -------------
        **kwargs: Any
            Custom number of keyword parameters which you want to update, these can be anything that is available during the object creation.

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

        await misc._update(self, **kwargs)
        # Update messages
        for message in self.messages:
            await message.update(_init_options={"parent" : self})

@misc.doc_category("Automatic generation")
class AutoGUILD:
    """
    .. versionadded:: v2.3

    Used for creating instances that will return
    guild objects.

    .. CAUTION::
        Any objects passed to AutoGUILD get **deep-copied** meaning, those same objects
        **will not be initialized** and cannot be used to obtain/change information regarding AutoGUILD.

        .. code-block::
            :caption: Illegal use of AutoGUILD
            :emphasize-lines: 6, 7

            auto_ch = daf.AutoCHANNEL(...)
            tm = daf.TextMESSAGE(..., channels=auto_ch)

            await daf.add_object(AutoGUILD(..., messages=[tm]))

            auto_ch.channels # Illegal (does not represent the same object as in AutoGUILD), results in exception
            await tm.update(...) # Illegal (does not represent the same object as in AutoGUILD), results in exception

        To actually modify message/channel objects inside AutoGUILD, you need to iterate thru each GUILD.

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
        Regex pattern to use when searching guild names that are to be included.
    exclude_pattern: Optional[str] = None
        Regex pattern to use when searching guild names that are **NOT** to be excluded.

        .. note::
            If both include_pattern and exclude_pattern yield a match, the guild will be
            excluded from match.

    remove_after: Optional[Union[timedelta, datetime]] = None
        When to remove this object from the shilling list.
    logging: Optional[bool] = False
        Set to True if you want the guilds generated to log
        sent messages.
    interval: Optional[timedelta] = timedelta(minutes=10)
        Interval at which to scan for new guilds
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
        "_safe_sem"
    )

    @typechecked
    def __init__(self,
                 include_pattern: str,
                 exclude_pattern: Optional[str] = None,
                 remove_after: Optional[Union[timedelta, datetime]] = None,
                 messages: Optional[List[BaseMESSAGE]] = [],
                 logging: Optional[bool] = False,
                 interval: Optional[timedelta] = timedelta(minutes=10)) -> None:
        self.include_pattern = include_pattern
        self.exclude_pattern = exclude_pattern
        self.remove_after = remove_after 
        self.messages = messages # Uninitialized template messages list that gets copied for each found guild.
        self.logging = logging
        self.interval = interval.total_seconds() # In seconds
        self.cache: Dict[GUILD] = {}
        self.last_scan = 0
        self._deleted = False
        self._created_at = datetime.now()
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
        if self._deleted:
            return False

        rm_after_type = type(self.remove_after)
        return (rm_after_type is timedelta and datetime.now() - self._created_at > self.remove_after or # The difference from creation time is bigger than remove_after
                rm_after_type is datetime and datetime.now() > self.remove_after) # The current time is larger than remove_after 

    async def initialize(self):
        "Initializes asynchronous elements."
        # Nothing is needed to be done here since everything is obtained from API wrapper cache.
        pass 
    
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

    async def _process(self):
        """
        Coroutine that finds new guilds from the
        API wrapper.
        """
        dcl = client.get_client()
        stamp = datetime.now().timestamp()
        if stamp - self.last_scan > self.interval:
            self.last_scan = stamp
            for dcgld in dcl.guilds:
                if (dcgld not in self.cache and 
                    re.search(self.include_pattern, dcgld.name) is not None and
                    (self.exclude_pattern is None or re.search(self.exclude_pattern, dcgld.name) is None)
                ):
                    try:
                        new_guild = GUILD(snowflake=dcgld,
                                                messages=deepcopy(self.messages),
                                                logging=self.logging)
                        await new_guild.initialize()
                        self.cache[dcgld] = new_guild
                    except Exception as exc:
                        trace(f"[AutoGUILD:] Unable to add new object.\nReason: {exc}",TraceLEVELS.WARNING)

    @misc._async_safe("_safe_sem", 1)
    async def _advertise(self, type_: AdvertiseTaskType):
        """
        Advertises thru all the GUILDs.

        Parameters
        ----------------
        type_: guild.AdvertiseTaskType
            Which task called this method.
            This is just forwarded to GUILDs' _advertise method.
        """
        await self._process()
        for g in self.guilds:
            await g._advertise(type_)

    @misc._async_safe("_safe_sem", 2)
    async def update(self, **kwargs):
        """
        Updates the object with new initialization parameters.

        .. WARNING::
            After calling this method the entire object is reset (this includes it's GUILD objects in cache).
        """
        if "interval" not in kwargs:
            kwargs["interval"] = timedelta(seconds=self.interval)

        return await misc._update(self, **kwargs)