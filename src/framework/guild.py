"""
    This module contains the class definitions for all things
    regarding the guild and also defines a USER class from the
    _BaseGUILD class.
"""
from    __future__ import annotations
import asyncio
from    contextlib import suppress
from    typing import Any, Literal, Union, List, Optional

from framework import misc
from    .exceptions import *
from    .tracing import *
from    .const import *
from    .message import *
from    . import client
from    . import sql
from    . import core
import  _discord as discord
import  time
import  json
import  pathlib
import  shutil

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


class _BaseGUILD:
    """ 
    Represents an universal guild.
    
    .. versionchanged:: 
        v2.0

            - Added the update method.
            - snowflake parameter can now be a discord.Object object.


    Parameters
    ---------------
    snowflake: Union[int, discord.Object]
        Discord's snowflake id or a Discord object that has the ID attribute.
    generate_log: bool
        Set to True if you wish to have message logs for this guild.
    """

    __slots__ = (       # Faster attribute access
        "apiobject",
        "logging",
        "_messages",
    )
    __logname__ = "_BaseGUILD" # Dummy to demonstrate correct definition for @sql._register_type decorator

    def __init__(self,
                 snowflake: Union[int, discord.Object],
                 messages: Optional[List]=[],
                 logging: Optional[bool]=False) -> None:

        self.apiobject: discord.Object = snowflake
        self.logging: bool= logging
        self._messages: list = messages  # Contains all the different message objects, this gets sorted in `.initialize()` method

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

    async def initialize(self):
        """
        Initializes the guild and then any message objects
        the guild may hold.
        """
        raise NotImplementedError

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

    async def generate_log(self,
                           message_context: dict) -> None:
        """
        Generates a .json type log or logs to a SQL database for each message send attempt.

        Prioritizes SQL logging.

        Parameter:
        -----------
        data_context: dict
            Dictionary containing data describing the message send attempt. (Return of ``message.send()``)
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
                        appender_data = json.load(appender)
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
                        appender_data["id"]   = guild_context["id"]
                        appender_data["type"] = guild_context["type"]
                        appender_data["message_history"] = []
                    finally:
                        appender.seek(0) # Reset cursor to the beginning of the file after reading

                    appender_data["message_history"].insert(0,
                        {
                            **message_context,
                            "index":    appender_data["message_history"][0]["index"] + 1 if len(appender_data["message_history"]) else 0,
                            "timestamp": timestamp
                        })                
                    json.dump(appender_data, appender, indent=4)
                    appender.truncate() # Remove any old data

        except Exception as exception:
            # Any uncaught exception (prevent from complete framework stop)
            trace(f"[{type(self).__name__}]: Unable to save log. Exception: {exception}", TraceLEVELS.WARNING)


@sql._register_type("GuildTYPE")
class GUILD(_BaseGUILD):
    """
    The GUILD object represents a server to which messages will be sent.
    
    .. versionchanged:: v2.0

        - Added the update method
        - Renamed param ``guild_id`` to ``snowflake``
        - Renamed ``generate_log`` parameter to ``logging``
        - snowflake parameter can now be a discord.Guild object.

    Parameters
    ------------
    snowflake: Union[int, discord.Guild]
        Discord's snowflake ID of the guild or discord.Guild object.
    messages: Optional[List[Union[TextMESSAGE, VoiceMESSAGE]]]
        Optional list of TextMESSAGE/VoiceMESSAGE objects.
    logging:  Optional[bool]
        Optional variable dictating whatever to log sent messages inside this guild.
    """
    
    __logname__ = "GUILD" # For sql._register_type
    __slots__   = (
        "t_messages",
        "vc_messages",
        "update_semaphore",
    )

    def __init__(self,
                 snowflake: Union[int, discord.Guild],
                 messages: Optional[List[Union[TextMESSAGE, VoiceMESSAGE]]]=[],
                 logging: Optional[bool]=False):
        super().__init__(snowflake, messages, logging)
        self.t_messages: List[TextMESSAGE] = []
        self.vc_messages: List[VoiceMESSAGE] = []
        misc._write_attr_once(self, "update_semaphore", asyncio.Semaphore(2))
    
    @property
    def _log_file_name(self):
        return "".join(char if char not in C_FILE_NAME_FORBIDDEN_CHAR else "#" for char in self.apiobject.name) + ".json"
    
    async def add_message(self, message: Union[TextMESSAGE, VoiceMESSAGE]):
        """
        Adds a message to the message list.

        Parameters
        --------------
        message: Union[TextMESSAGE, VoiceMESSAGE]
            Message object to add.

        Raises
        --------------
        DAFParameterError(code=DAF_INVALID_TYPE)
            Raised when the message is not of type TextMESSAGE or VoiceMESSAGE.
        Other
            Raised from message.initialize() method.
        """
        if not isinstance(message, (TextMESSAGE, VoiceMESSAGE)):
            raise DAFParameterError(f"Invalid xxxMESSAGE type: {type(message).__name__}, expected  {TextMESSAGE.__name__} or {VoiceMESSAGE.__name__}", DAF_INVALID_TYPE)

        await message.initialize()

        if isinstance(message, TextMESSAGE):
            self.t_messages.append(message)
        elif isinstance(message, VoiceMESSAGE):
            self.vc_messages.append(message)

    def remove_message(self, message: Union[TextMESSAGE, VoiceMESSAGE]):
        """
        Removes a message from the message list.

        Parameters
        --------------
        message: Union[TextMESSAGE, VoiceMESSAGE]
            Message object to remove.

        Raises
        --------------
        DAFParameterError(code=DAF_INVALID_TYPE)
            Raised when the message is not of type TextMESSAGE or VoiceMESSAGE.
        ValueError
            Raised when the message is not present in the list.
        """
        if isinstance(message, TextMESSAGE):
            message._delete()
            self.t_messages.remove(message)
            return
        elif isinstance(message, VoiceMESSAGE):
            message._delete()
            self.vc_messages.remove(message)
            return

        raise DAFParameterError(f"Invalid xxxMESSAGE type: {type(message).__name__}, expected  {TextMESSAGE.__name__} or {VoiceMESSAGE.__name__}", DAF_INVALID_TYPE)

    async def initialize(self) -> None:
        """
        This function initializes the API related objects and then tries to initialize the MESSAGE objects.

        Raises
        -----------
        DAFNotFoundError(code=DAF_GUILD_ID_NOT_FOUND)
            Raised when the guild_id wasn't found.

        Other
            Raised from .add_message(message_object) method.
        """
        guild_id = self.snowflake
        if isinstance(self.apiobject, int):
            cl = client.get_client()
            self.apiobject = cl.get_guild(guild_id)

        if self.apiobject is not None:
            for message in self._messages:
                await self.add_message(message)

            self._messages.clear()
            return

        raise DAFNotFoundError(f"Unable to find guild with ID: {guild_id}", DAF_GUILD_ID_NOT_FOUND)

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
        msg_list = self.t_messages if mode == "text" else self.vc_messages
        for message in msg_list[:]: # Copy the avoid issues with the list being modified while iterating (add_message/remove_message)
            if message.is_ready():
                message.reset_timer()
                message_ret = await message.send()
                # Check if the message still has any channels (as they can be auto removed on 404 status)
                if not len(message.channels) and message in msg_list:
                    self.remove_message(message) # All channels were removed (either not found or forbidden) -> remove message from send list
                    trace(f"[GUILD]: Removing a {type(message).__name__} because it's channels were removed, in guild {self.apiobject.name}(ID: {self.snowflake})", TraceLEVELS.WARNING)
                if self.logging and message_ret is not None:
                    await self.generate_log(message_ret)              
            

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
        DAFParameterError(code=DAF_UPDATE_PARAMETER_ERROR)
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
            await message.update()
        

@sql._register_type("GuildTYPE")
class USER(_BaseGUILD):
    """
    The USER object represents a user to whom messages will be sent.
    
    .. versionchanged:: v2.0

        - ``user_id`` parameter renamed to ``snowflake``
        - ``snowflake`` can now also be a ``discord.User`` object
        - renamed ``generate_log`` parameter to ``logging``.

    Parameters
    ------------
    snowflake: Union[int, discord.User]
        Discord's snowflake ID of the user or discord.User object.
    messages: Optional[List[DirectMESSAGE]]
        Optional list of DirectMESSAGE objects.
    logging: Optional[bool]
        Optional variable dictating whatever to log sent messages inside this guild.
    """

    __logname__ = "USER" # For sql._register_type
    __slots__   = (
        "t_messages",
        "update_semaphore",
    )

    @property
    def _log_file_name(self):
        return "".join(char if char not in C_FILE_NAME_FORBIDDEN_CHAR else "#" for char in f"{self.apiobject.display_name}#{self.apiobject.discriminator}") + ".json"

    def __init__(self,
                 snowflake: Union[int, discord.User],
                 messages: Optional[List[DirectMESSAGE]]=[],
                 logging: Optional[bool] = False) -> None:
        super().__init__(snowflake, messages, logging)
        self.t_messages: List[DirectMESSAGE] = []
        
        misc._write_attr_once(self, "update_semaphore", asyncio.Semaphore(2)) # Only allows re-referencing this attribute once

    async def add_message(self, message):
        """
        Adds a message to the message list.

        Parameters
        --------------
        message: DirectMESSAGE
            Message object to add.

        Raises
        --------------
        DAFParameterError(code=DAF_INVALID_TYPE)
            Raised when the message is not of type DirectMESSAGE.
        Other
            Raised from message.initialize() method.
        """
        if not isinstance(message, DirectMESSAGE):
            raise DAFParameterError(f"Invalid xxxMESSAGE type: {type(message).__name__}, expected  {DirectMESSAGE.__name__}", DAF_INVALID_TYPE)

        await message.initialize(user=self.apiobject)
        self.t_messages.append(message)

    
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
        DAFParameterError(code=DAF_INVALID_TYPE)
            Raised when the message is not of type DirectMESSAGE.
        """
        if isinstance(message, DirectMESSAGE):
            message._delete()
            self.t_messages.remove(message)
            return

        raise DAFParameterError(f"Invalid xxxMESSAGE type: {type(message).__name__}, expected  {DirectMESSAGE.__name__}", DAF_INVALID_TYPE)

    async def initialize(self):
        """
        This function initializes the API related objects and then tries to initialize the MESSAGE objects.

        Raises
        -----------
        DAFNotFoundError(code=DAF_USER_CREATE_DM)
            Raised when the DM could not be created.
        Other
            Raised from .add_message(message_object) method.
        """
        user_id = self.snowflake
        if isinstance(self.apiobject, int):
            cl = client.get_client()
            self.apiobject = await cl.get_or_fetch_user(user_id) # Get object from cache

        # Api object was found in cache or fetched from API -> initialize messages
        if self.apiobject is not None:
            for message in self._messages:
                await self.add_message(message)

            self._messages.clear()
            return

        # Api object wasn't found, even after direct API call to discord.
        raise DAFNotFoundError(f"[USER]: Unable to create DM with user id: {user_id}", DAF_USER_CREATE_DM)

    @misc._async_safe("update_semaphore", 1)
    async def advertise(self,
                        mode: Literal["text", "voice"]) -> None:
        """
        Main coroutine responsible for sending all the messages to this specific guild,
        it is called from the core module's advertiser task.
        
        Parameters
        --------------
        mode: Literal["text", "voice"]
            Tells which task called this method (there is one task for textual messages and one for voice like messages).
        """
        if mode == "text":  # Does not have voice messages, only text based (DirectMESSAGE)
            for message in self.t_messages[:]: # Copy the avoid issues with the list being modified while iterating (add_message/remove_message)
                if message.is_ready():
                    message.reset_timer()
                    message_ret = await message.send()
                    if message_ret is not None:
                        if self.logging:
                            await self.generate_log(message_ret)

                        if message.deleted:  # Only True on critical errors that need to be handled by removing all messages
                            for msg in self.t_messages:
                                self.remove_message(msg)

                            trace(f"Removing all messages for user {self.apiobject.display_name}#{self.apiobject.discriminator} (ID: {self.snowflake}) because we do not have permissions to send to that user.", TraceLEVELS.WARNING)
                            break
    
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
        DAFParameterError(code=DAF_UPDATE_PARAMETER_ERROR)
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
            await message.update(init_options={"user" : self.apiobject})