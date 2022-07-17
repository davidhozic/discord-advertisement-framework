"""
    ~  guild  ~
    This module contains the class defitions for all things
    regarding the guild and also defines a USER class from the
    BaseGUILD class.
"""

from    contextlib import suppress
from    typing import Any, Literal, Union, List, Optional
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
    """ ~  class  ~
    - @Info: Contains the global variables for the module"""
    server_log_path = None


class BaseGUILD:
    """ ~ class ~
    - @Info: BaseGUILD object is used for creating inherited classes that work like a guild
    - @Param: 
        - snowflake    ~ The snowflake of the guild
        - generate_log ~ Whether or not to generate a log file for the guild"""

    __slots__ = (       # Faster attribute access
        "apiobject",
        "snowflake",
        "logging",
        "_messages",
    )
    __logname__ = "BaseGUILD" # Dummy to demonstrate correct definition for @sql.register_type decorator

    @property
    def log_file_name(self):
        """~ property (getter) ~
        - @Info: The method returns a string that transforms the xGUILD's discord name into
               a string that contains only allowed character. This is a method instead of
               property because the name can change overtime."""
        raise NotImplementedError
    
    @property
    def messages(self) -> List[BaseMESSAGE]:
        """
        ~ property (getter) ~
        - @Info: Returns all the messages inside the object.
        """
        return self.t_messages + self.vc_messages

    def __init__(self,
                 snowflake: Any,
                 messages: Optional[List]=[],
                 logging: Optional[bool]=False) -> None:

        self.apiobject: discord.Snowflake = None
        self.snowflake: Any = snowflake
        self.logging: bool= logging
        self._messages: list = messages

    def __eq__(self, other) -> bool:
        """
        ~  operator method  ~
        - @Return: ~ Returns True if objects have the same snowflake or False otherwise
        - @Info:   The function is used to compare two objects"""
        return self.snowflake == other.snowflake

    async def add_message(self, message):
        """~  coro  ~
        - @Info:   Adds a message to the message list
        - @Param:  message ~ message object to add"""
        raise NotImplementedError

    async def initialize(self):
        """~  coro  ~
        - @Return: bool:
                - Returns True if the initialization was successful
                - Returns False if failed, indicating the object should be removed from the server_list
        - @Info: The function initializes all the <IMPLEMENTATION> objects (and other objects inside the  <IMPLEMENTATION> object reccurssively).
                 It tries to get the  discord.<IMPLEMENTATION> object from the self.<implementation>_id and then tries to initialize the MESSAGE objects."""
        raise NotImplementedError

    async def advertise(self,
                        mode: Literal["text", "voice"]):
        """~ async method
        - @Info:
            - This is the main coroutine that is responsible for sending all the messages to this specificc guild,
              it is called from the core module's advertiser task
        """
        raise NotImplementedError

    async def update(self, **kwargs):
        """ ~ async method ~
        - @Added in v1.9.5
        - @Info:
            Used for chaning the initialization parameters the object was initialized with.
            NOTE: Upon updating, the internal state of objects get's reset, meaning you basically have a brand new created object.
        - @Params:
            - The allowed parameters are the initialization parameters first used on creation of the object
        - @Exception:
            - <class DAFInvalidParameterError code=DAF_UPDATE_PARAMETER_ERROR> ~ Invalid keyword argument was passed
            - Other exceptions raised from .initialize() method"""
        raise NotImplementedError

    async def generate_log(self,
                           message_context: dict) -> None:
        """~ async method
        - @Param:
            - data_context  ~ string representation of sent data, which is the return data of xxxMESSAGE.send()
        - @Info:   Generates a log of a xxxxMESSAGE send attempt either in file or in a SQL database"""

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
                not await manager.save_log(guild_context, message_context)
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

                logging_output = str(logging_output.joinpath(self.log_file_name))

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
            # Any uncautch exception (prevent from complete framework stop)
            trace(f"[{type(self).__name__}]: Unable to save log. Exception: {exception}", TraceLEVELS.WARNING)


@sql.register_type("GuildTYPE")
class GUILD(BaseGUILD):
    """
    The GUILD object represents a server to which messages will be sent.
    
    Parameters
    ------------
    - snowflake: `Union[int, discord.Guild]` - Discord's snowflake identificator of the guild or discord.Guild object,
    - messages: `Optional[List[Union[TextMESSAGE, VoiceMESSAGE]]]` - Optional list of TextMESSAGE/VoiceMESSAGE objects
    - logging:  `Optional[bool]` - Optional variable dictating whatever to log sent't messages inside this guild."""
    
    __logname__ = "GUILD" # For sql.register_type
    __slots__   = (
        "t_messages",
        "vc_messages"
    )

    def __init__(self,
                 snowflake: Union[int, discord.Guild],
                 messages: Optional[List[Union[TextMESSAGE, VoiceMESSAGE]]]=[],
                 logging: Optional[bool]=False):
        super().__init__(snowflake, messages, logging)
        self.t_messages: List[TextMESSAGE] = []
        self.vc_messages: List[VoiceMESSAGE] = []
    
    @property
    def log_file_name(self):
        """~ property (getter) ~
        - @Info: The method returns a string that transforms the GUILD's discord name into
               a string that contains only allowed character. This is a method instead of
               property because the name can change overtime."""
        return "".join(char if char not in C_FILE_NAME_FORBIDDEN_CHAR else "#" for char in self.apiobject.name) + ".json"
    
    async def add_message(self, message: Union[TextMESSAGE, VoiceMESSAGE]):
        """~  coro  ~
        - @Info:   Adds a message to the message list
        - @Param:  message ~ message object to add
        - @Exceptions:
            - <class DAFInvalidParameterError code=DAF_INVALID_TYPE> ~ Raised when the message is not of type TextMESSAGE or VoiceMESSAGE
            - Other exceptions from message.initialize() method"""
        if not isinstance(message, (TextMESSAGE, VoiceMESSAGE)):
            raise DAFInvalidParameterError(f"Invalid xxxMESSAGE type: {type(message).__name__}, expected  {TextMESSAGE.__name__} or {VoiceMESSAGE.__name__}", DAF_INVALID_TYPE)

        await message.initialize()

        if isinstance(message, TextMESSAGE):
            self.t_messages.append(message)
        elif isinstance(message, VoiceMESSAGE):
            self.vc_messages.append(message)

    def remove_message(self, message: Union[TextMESSAGE, VoiceMESSAGE]):
        """~ method ~
        - @Info:   Removes a message from the message list
        - @Param:  message ~ message object to remove
        - @Exceptions:
            - <class DAFInvalidParameterError code=DAF_INVALID_TYPE> ~ Raised when the message is not of type TextMESSAGE or VoiceMESSAGE"""
        if isinstance(message, TextMESSAGE):
            self.t_messages.remove(message)
            return
        elif isinstance(message, VoiceMESSAGE):
            self.vc_messages.remove(message)
            return

        raise DAFInvalidParameterError(f"Invalid xxxMESSAGE type: {type(message).__name__}, expected  {TextMESSAGE.__name__} or {VoiceMESSAGE.__name__}", DAF_INVALID_TYPE)

    async def initialize(self):
        """ ~ async method
        - @Info:   This function initializes the API related objects and then tries to initialize the MESSAGE objects.
        - @Exceptions:
            - <class DAFNotFoundError code=DAF_GUILD_ID_NOT_FOUND> ~ Raised when the guild_id wasn't found
            - Other exceptions from .add_message(message_object) method"""
        if isinstance(self.snowflake, int):
            guild_id = self.snowflake
            cl = client.get_client()
            self.apiobject = cl.get_guild(guild_id)
        else:
            self.apiobject = self.snowflake
            self.snowflake = self.apiobject.id

        if self.apiobject is not None:
            for message in self._messages:
                await self.add_message(message)

            return

        raise DAFNotFoundError(f"Unable to find guild with ID: {guild_id}", DAF_GUILD_ID_NOT_FOUND)

    async def advertise(self,
                        mode: Literal["text", "voice"]):
        """~ async method
        - @Info:
            - This is the main coroutine that is responsible for sending all the messages to this specificc guild,
              it is called from the core module's advertiser task"""
        msg_list = self.t_messages if mode == "text" else self.vc_messages
        marked_del = []

        for message in msg_list: # Copy the avoid issues with the list being modified while iterating
            if message.is_ready():
                message.reset_timer()
                message_ret = await message.send()
                # Check if the message still has any channels (as they can be auto removed on 404 status)
                if len(message.channels) == 0:
                    marked_del.append(message) # All channels were removed (either not found or forbidden) -> remove message from send list
                if self.logging and message_ret is not None:
                    await self.generate_log(message_ret)

        # Cleanup messages marked for removal
        for message in marked_del:
            if message in msg_list:
                msg_list.remove(message)
            trace(f"[GUILD]: Removing a {type(message).__name__} because it's channels were removed, in guild {self.apiobject.name}(ID: {self.snowflake})", TraceLEVELS.WARNING)

    async def update(self, **kwargs):
        """ ~ async method ~
        - @Added in v1.9.5
        - @Info:
            Used for chaning the initialization parameters the object was initialized with.
            First the guild is updated and then all the message objects are updated.
            NOTE: Upon updating, the internal state of objects get's reset, meaning you basically have a brand new created object.
        - @Params:
            - The allowed parameters are the initialization parameters first used on creation of the object
        - @Exception:
            - <class DAFInvalidParameterError code=DAF_UPDATE_PARAMETER_ERROR> ~ Invalid keyword argument was passed
            - Other exceptions raised from .initialize() method"""
        # Update the guild
        if "guild_id" not in kwargs:
            kwargs["guild_id"] = self.snowflake
        await core.update(self, **kwargs)
        # Update messages
        for message in self.messages:
            await message.update()
        

@sql.register_type("GuildTYPE")
class USER(BaseGUILD):
    """
    The USER object represents a user to whom messages will be sent.
    
    Parameters
    ------------
    - snowflake: `Union[int, discord.User]` - Discord's snowflake identificator of the user or discord.User object,
    - messages: `Optional[List[DirectMESSAGE]]` - Optional list of DirectMESSAGE objects
    - logging:  `Optional[bool]` - Optional variable dictating whatever to log sent't messages inside this guild."""

    __logname__ = "USER" # For sql.register_type
    __slots__   = (
        "t_messages",
    )

    @property
    def log_file_name(self):
        """~ property (getter) ~
        - @Info: The method returns a string that transforms the USER's discord name into
               a string that contains only allowed character. This is a method instead of
               property because the name can change overtime."""
        return "".join(char if char not in C_FILE_NAME_FORBIDDEN_CHAR else "#" for char in f"{self.apiobject.display_name}#{self.apiobject.discriminator}") + ".json"

    def __init__(self,
                 snowflake: Union[int, discord.User],
                 messages: Optional[List[DirectMESSAGE]]=[],
                 logging: Optional[bool] = False) -> None:
        super().__init__(snowflake, messages, logging)
        self.t_messages: List[DirectMESSAGE] = []

    async def add_message(self, message):
        """~  coro  ~
        - @Info:   Adds a message to the message list
        - @Param:  message ~ message object to add
        - @Exceptions:
            - <class DAFInvalidParameterError code=DAF_INVALID_TYPE> ~ Raised when the message is not of type DirectMESSAGE
            - Other exceptions from message.initialize() method
        """
        if not isinstance(message, DirectMESSAGE):
            raise DAFInvalidParameterError(f"Invalid xxxMESSAGE type: {type(message).__name__}, expected  {DirectMESSAGE.__name__}", DAF_INVALID_TYPE)

        await message.initialize(user=self.apiobject)
        self.t_messages.append(message)

    async def initialize(self):
        """ ~ async method
        - @Info: This function initializes the API related objects and then tries to initialize the MESSAGE objects.
        - @Exceptions:
            - <class DAFNotFoundError code=DAF_USER_CREATE_DM> ~ Raised when the user_id wasn't found
            - Other exceptions from .add_message(message_object) method
        """
        if isinstance(self.snowflake, int):
            user_id = self.snowflake
            cl = client.get_client()
            self.apiobject = cl.get_or_fetch_user(user_id) # Get object from cache
        else:
            self.apiobject = self.snowflake
            self.snowflake = self.apiobject.id

        # Api object was found in cache or fetched from API -> initialize messages
        if self.apiobject is not None:
            for message in self._messages:
                await self.add_message(message)

            return

        # Api object wasn't found, even after direct API call to discord.
        raise DAFNotFoundError(f"[USER]: Unable to create DM with user id: {user_id}", DAF_USER_CREATE_DM)

    async def advertise(self,
                        mode: Literal["text", "voice"]) -> None:
        """ ~ async method
        - @Info:
            - This is the main coroutine that is responsible for sending all the messages to this specificc guild,
              it is called from the core module's advertiser task"""
        if mode == "text":  # Does not have voice messages, only text based (DirectMESSAGE)
            for message in self.t_messages: # Copy the avoid issues with the list being modified while iterating
                if message.is_ready():
                    message.reset_timer()
                    message_ret = await message.send()
                    if self.logging and message_ret is not None:
                        await self.generate_log(message_ret)
                    
                    if message.dm_channel is None:
                        self.t_messages.clear()            # Remove all messages since that they all share the same user and will fail
                        trace(f"Removing all messages for user {self.apiobject.display_name}#{self.apiobject.discriminator} (ID: {self.snowflake}) because we do not have permissions to send to that user.", TraceLEVELS.WARNING)
                        break
    
    async def update(self, **kwargs):
        """ ~ async method ~
        - @Added in v1.9.5
        - @Info:
            Used for chaning the initialization parameters the object was initialized with.
            First the user is updated and then all the message objects are updated.
            NOTE: Upon updating, the internal state of objects get's reset, meaning you basically have a brand new created object.
        - @Params:
            - The allowed parameters are the initialization parameters first used on creation of the object
        - @Exception:
            - <class DAFInvalidParameterError code=DAF_UPDATE_PARAMETER_ERROR> ~ Invalid keyword argument was passed
            - Other exceptions raised from .initialize() method"""
        # Update the guild
        if "user_id" not in kwargs:
            kwargs["user_id"] = self.snowflake
        await core.update(self, **kwargs)
        # Update messages
        for message in self.messages:
            await message.update(init_options={"user" : self.apiobject})