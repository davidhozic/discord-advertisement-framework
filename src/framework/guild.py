"""
    This module contains the class definitions for all things
    regarding the guild and also defines a USER class from the
    _BaseGUILD class.
"""
from __future__ import annotations
import asyncio
from contextlib import suppress
from typing import Any, Coroutine, Literal, Union, List, Optional, Dict, Callable
from typeguard import typechecked
from datetime import timedelta, datetime

from .exceptions import *
from .tracing import *
from .const import *
from .message import *

from . import client
from . import sql
from . import core
from . import misc

import _discord as discord
import time
import json
import pathlib
import shutil

__all__ = (
    "GUILD",
    "USER"
)

#######################################################################
# Globals
#######################################################################
class GLOBALS:
    """
    Contains the global variables for the module.
    """
    server_log_path = None

@typechecked
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
    remove_after: Optional[Union[int, timedelta, datetime]]
        Deletes the message after:

        * int - N sends, where each send of all TextMESSAGE objects and each send of all  counts decrements the counter.
        * timedelta - the specified time difference
        * datetime - specific date & time
    """

    __slots__ = (       # Faster attribute access
        "apiobject",
        "logging",
        "_messages_uninitialized",
        "message_dict",
        "remove_after",
        "_created_at"
    )
    __logname__ = "_BaseGUILD" # Dummy to demonstrate correct definition for @sql._register_type decorator
    
    def __init__(self,
                 snowflake: Any,
                 messages: Optional[List]=[],
                 logging: Optional[bool]=False,
                 remove_after: Optional[Union[int, timedelta, datetime]]=None) -> None:

        self.apiobject: discord.Object = snowflake
        self.logging: bool= logging
        self._messages_uninitialized: list = messages   # Contains all the different message objects, this gets sorted in `.initialize()` method
        self.message_dict: Dict[str, List[BaseMESSAGE]] = {"text": [], "voice": []}  # Dictionary, which's keys hold the discord message type(text, voice) and keys are a list of messages
        self.remove_after = remove_after  # int - after n sends; timedelta - after amount of time; datetime - after that time
        self._created_at = datetime.now() # The time this object was created

    @property
    def _log_file_name(self):
        """
        Returns a string that transforms the xGUILD's discord name into
        a string that contains only allowed character. This is a method instead of
        property because the name can change overtime.
        """
        raise NotImplementedError

    @property
    def messages(self) -> List[BaseMESSAGE]:
        """
        Returns all the (initialized) message objects inside the object.

        .. versionadded:: v2.0
        """
        ret = []
        for x in self.__slots__:
            if hasattr(self, x) and not x.startswith("_") and x.endswith("messages"):
                ret.extend(getattr(self , x))
        return ret

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
        return (rm_after_type is int and self.remove_after == 0 or # Remove after N attempts, self.remove_after is decremented in .advertise
                rm_after_type is timedelta and datetime.now() - self._created_at > self.remove_after or # The difference from creation time is bigger than remove_after
                rm_after_type is datetime and datetime.now() > self.remove_after) # The current time is larger than remove_after

    def __eq__(self, other: _BaseGUILD) -> bool:
        """
        Compares two guild objects if they're equal.
        """
        return self.snowflake == other.snowflake

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
        DAFNotFoundError(code=DAF_SNOWFLAKE_NOT_FOUND)
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
                await self.add_message(message)

            self._messages_uninitialized.clear()
            return

        raise DAFNotFoundError(f"Unable to find object with ID: {guild_id}", DAF_SNOWFLAKE_NOT_FOUND)

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
    async def advertise(self,
                        mode: Literal["text", "voice"]):
        """
        Main coroutine responsible for sending all the messages to this specific guild,
        it is called from the core module's advertiser task.

        Parameters
        --------------
        mode: Literal["text", "voice"]
            Tells which task called this method (there is one task for textual messages and one for voice like messages).
        """
        msg_list = self.message_dict[mode]
        for message in msg_list[:]: # Copy the avoid issues with the list being modified while iterating (add_message/remove_message)
            if message.is_ready():
                message.reset_timer()
                message_ret = await message._send()
                       
                # Remove message
                if message._check_state():
                    self.remove_message(message)

                # Generate log (JSON or SQL)
                if self.logging and message_ret is not None:
                    await self._generate_log(message_ret)

                # Remove this object from the shill list due to exceeded amounts of sends
                if type(self.remove_after) is int:
                    self.remove_after -= 1

                if self._check_state():
                    trace(f"[GUILD:] Removing GUILD object representing {self.apiobject}")
                    core.remove_object(self)

    async def _generate_log(self,
                           message_context: dict) -> None:
        """
        Generates a .json type log or logs to a SQL database for each message send attempt.

        Prioritizes SQL logging.

        Parameter:
        -----------
        data_context: dict
            Dictionary containing data describing the message send attempt. (Return of ``message._send()``)
        """
        guild_context = {
            "name" : str(self.apiobject),
            "id" : self.snowflake,
            "type" : type(self).__logname__,
        }

        try:
            # Try to obtain the sql manager. If it returns None (sql logging disabled), save into file
            manager = sql.get_sql_manager()
            if (
                manager is None or  # Short circuit evaluation
                not await manager._save_log(guild_context, message_context)
            ):
                timestruct = time.localtime()
                timestamp = "{:02d}.{:02d}.{:04d} {:02d}:{:02d}:{:02d}".format(timestruct.tm_mday,
                                                                            timestruct.tm_mon,
                                                                            timestruct.tm_year,
                                                                            timestruct.tm_hour,
                                                                            timestruct.tm_min,
                                                                            timestruct.tm_sec)
                logging_output = pathlib.Path(GLOBALS.server_log_path)\
                            .joinpath("{:02d}".format(timestruct.tm_year))\
                            .joinpath("{:02d}".format(timestruct.tm_mon))\
                            .joinpath("{:02d}".format(timestruct.tm_mday))
                with suppress(FileExistsError):
                    logging_output.mkdir(parents=True,exist_ok=True)

                logging_output = str(logging_output.joinpath(self._log_file_name))

                # Create file if it doesn't exist
                fresh_file = False
                with suppress(FileExistsError), open(logging_output, "x", encoding="utf-8"):
                    fresh_file = True

                # Write to file
                with open(logging_output,'r+', encoding='utf-8') as appender:
                    appender_data = None
                    appender.seek(0) # Append moves cursor to the end of the file
                    try:
                        appender_data: dict = json.load(appender)
                    except json.JSONDecodeError:
                        # No valid json in the file, create new data
                        # and create a .old file to store this invalid data
                        # Copy-paste to .old file to prevent data loss
                        if not fresh_file: ## Failed because the file was just created, no need to copy-paste
                            # File not newly created, and has invalid data
                            shutil.copyfile(logging_output, f"{logging_output}.old")
                        # Create new data
                        appender_data = {}
                        appender_data["name"] = guild_context["name"]
                        appender_data["id"] = guild_context["id"]
                        appender_data["type"] = guild_context["type"]
                        appender_data["message_history"] = []
                    finally:
                        appender.seek(0) # Reset cursor to the beginning of the file after reading

                    appender_data["message_history"].insert(0,
                        {
                            **message_context,
                            "index": appender_data["message_history"][0]["index"] + 1 if len(appender_data["message_history"]) else 0,
                            "timestamp": timestamp
                        })
                    json.dump(appender_data, appender, indent=4)
                    appender.truncate() # Remove any old data

        except Exception as exception:
            # Any uncaught exception (prevent from complete framework stop)
            trace(f"[{type(self).__name__}]: Unable to save log. Exception: {exception}", TraceLEVELS.WARNING)


@typechecked
@sql._register_type("GuildTYPE")
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
    remove_after: Optional[Union[int, timedelta, datetime]]
        Deletes the message after:

        * int - N sends, where each send of all TextMESSAGE objects and each send of all  counts decrements the counter.
        * timedelta - the specified time difference
        * datetime - specific date & time
    """

    __logname__ = "GUILD" # For sql._register_type
    __slots__ = (
        "update_semaphore",
    )

    def __init__(self,
                 snowflake: Union[int, discord.Guild],
                 messages: Optional[List[Union[TextMESSAGE, VoiceMESSAGE]]]=[],
                 logging: Optional[bool]=False,
                 remove_after: Optional[Union[int, timedelta, datetime]]=None):
        super().__init__(snowflake, messages, logging, remove_after)
        misc._write_attr_once(self, "update_semaphore", asyncio.Semaphore(2))

    @property
    def _log_file_name(self):
        return "".join(char if char not in C_FILE_NAME_FORBIDDEN_CHAR else "#" for char in self.apiobject.name) + ".json"

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
        await message.initialize(guild=self.apiobject)
        self.message_dict["text" if isinstance(message, TextMESSAGE) else "voice"].append(message)

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
        message._delete()
        self.message_dict["text" if isinstance(message, TextMESSAGE) else "voice"].remove(message)

    async def initialize(self) -> None:
        """
        This function initializes the API related objects and then tries to initialize the MESSAGE objects.

        .. note::
            This should NOT be manually called, it is called automatically after adding the message.

        Raises
        -----------
        DAFNotFoundError(code=DAF_SNOWFLAKE_NOT_FOUND)
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

        await core._update(self, **kwargs)
        # Update messages
        for message in self.messages:
            await message.update(_init_options={"guild": self.apiobject})


@typechecked
@sql._register_type("GuildTYPE")
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
    remove_after: Optional[Union[int, timedelta, datetime]]
        Deletes the message after:

        * int - N sends, where each send of all TextMESSAGE objects and each send of all  counts decrements the counter.
        * timedelta - the specified time difference
        * datetime - specific date & time
    """

    __logname__ = "USER" # For sql._register_type
    __slots__ = (
        "update_semaphore",
    )

    @property
    def _log_file_name(self):
        return "".join(char if char not in C_FILE_NAME_FORBIDDEN_CHAR else "#" for char in f"{self.apiobject.display_name}#{self.apiobject.discriminator}") + ".json"

    def __init__(self,
                 snowflake: Union[int, discord.User],
                 messages: Optional[List[DirectMESSAGE]]=[],
                 logging: Optional[bool] = False,
                 remove_after: Optional[Union[int, timedelta, datetime]]=None) -> None:
        super().__init__(snowflake, messages, logging, remove_after)
        misc._write_attr_once(self, "update_semaphore", asyncio.Semaphore(2)) # Only allows re-referencing this attribute once

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
        await message.initialize(user=self.apiobject)
        self.message_dict["text"].append(message)

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
        message._delete()
        self.t_messages.remove(message)

    async def initialize(self):
        """
        This function initializes the API related objects and then tries to initialize the MESSAGE objects.

        Raises
        -----------
        DAFNotFoundError(code=DAF_SNOWFLAKE_NOT_FOUND)
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

        await core._update(self, **kwargs)
        # Update messages
        for message in self.messages:
            await message.update(_init_options={"user" : self.apiobject})
