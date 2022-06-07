"""
    ~  guild  ~
    This module contains the class defitions for all things
    regarding the guild and also defines a USER class from the
    BaseGUILD class.
"""

from    contextlib import suppress
from    typing import Literal, Union, List
from    .tracing import *
from    .const import *
from    .message import *
from    . import client
from    . import sql
import  time
import  json
import  pathlib

__all__ = (
    "GUILD",
    "USER"
)

#######################################################################
# Globals
#######################################################################
class GLOBALS:
    """ ~  GLOBALS  ~
        Contains the global variables for the module"""
    server_log_path = None


class BaseGUILD:
    """ ~ BaseGUILD ~
        BaseGUILD object is used for creating inherited classes that work like a guild"""

    __slots__ = (       # Faster attribute access
        "initialized",
        "apiobject",
        "snowflake",
        "_generate_log",
        "_messages",
        "t_messages",
        "vc_messages"
    )
    __logname__ = "BaseGUILD"

    @property
    def log_file_name(self):
        """~ property (getter) ~
        @Info: The method returns a string that transforms the xGUILD's discord name into
               a string that contains only allowed character. This is a method instead of
               property because the name can change overtime."""
        raise NotImplementedError

    def __init__(self,
                 snowflake: int,
                 generate_log: bool=False) -> None:
        self.initialized = False
        self.apiobject = None
        self.snowflake = snowflake
        self._generate_log = generate_log
        self.t_messages: List[Union[TextMESSAGE, DirectMESSAGE]] = []
        self.vc_messages: List[VoiceMESSAGE] = []

    def __eq__(self, other) -> bool:
        """
        ~  __eq__  ~
        @Return: bool - Returns True if objects have the same snowflake
        @Info:   The function is used to compare two objects
        """
        return self.snowflake == other.snowflake

    async def add_message(self, message):
        """~  add_message  ~
        @Info:   Adds a message to the message list
        @Param:  message ~ message object to add
        """
        raise NotImplementedError

    async def initialize(self) -> bool:
        """
        ~  initialize  ~
        @Return: bool:
                - Returns True if the initialization was successful
                - Returns False if failed, indicating the object should be removed from the server_list
        @Info:   The function initializes all the <IMPLEMENTATION> objects (and other objects inside the  <IMPLEMENTATION> object reccurssively).
                 It tries to get the  discord.<IMPLEMENTATION> object from the self.<implementation>_id and then tries to initialize the MESSAGE objects.
        """
        raise NotImplementedError

    async def advertise(self,
                        mode: Literal["text", "voice"]):
        """
            ~ advertise ~
            @Info:
            This is the main coroutine that is responsible for sending all the messages to this specificc guild,
            it is called from the core module's advertiser task
        """
        raise NotImplementedError

    async def generate_log(self,
                           message_context: dict) -> None:
        """
        Name:   generate_log
        Param:
            - data_context  - str representation of sent data, which is return data of xxxMESSAGE.send()
        Info:   Generates a log of a xxxxMESSAGE send attempt
        """

        guild_context = {
            "name" : str(self.apiobject),
            "id" : self.snowflake,
            "type" : type(self).__logname__,
        }

        try:
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

                # with suppress(FileExistsError):
                #     with open(logging_output,'x', encoding='utf-8'):
                #         pass

                with open(logging_output,'a+', encoding='utf-8') as appender:
                    appender_data = None
                    appender.seek(0)
                    try:
                        appender_data = json.load(appender)
                    except json.JSONDecodeError:
                        appender_data = {}
                        appender_data["name"] = guild_context["name"]
                        appender_data["id"]   = guild_context["id"]
                        appender_data["type"] = guild_context["type"]
                        appender_data["message_history"] = []
                    finally:
                        appender.seek(0)
                        appender.truncate(0)

                    appender_data["message_history"].insert(0,
                        {
                            **message_context,
                            "index":    appender_data["message_history"][0]["index"] + 1 if len(appender_data["message_history"]) else 0,
                            "timestamp": timestamp
                        })
                    json.dump(appender_data, appender, indent=4)

        except Exception as exception:
            trace(f"[{type(self).__name__}]: Unable to save log. Exception: {exception}", TraceLEVELS.WARNING)


@sql.register_type("GuildTYPE")
class GUILD(BaseGUILD):
    """
    Name: GUILD
    Info: The GUILD object represents a server to which messages will be sent.
    Params:
    - Guild ID - identificator which can be obtained by enabling developer mode in discord's settings and
                 afterwards right-clicking on the server/guild icon in the server list and clicking "Copy ID",
    - List of TextMESSAGE/VoiceMESSAGE objects
    - Generate file log - bool variable, if True it will generate a file log for each message send attempt.
    """
    __logname__ = "GUILD"
    __slots__   = set()  # Removes __dict__ (prevents dynamic attributes)

    @property
    def log_file_name(self):
        """~ property (getter) ~
        @Info: The method returns a string that transforms the GUILD's discord name into
               a string that contains only allowed character. This is a method instead of
               property because the name can change overtime."""
        return "".join(char if char not in C_FILE_NAME_FORBIDDEN_CHAR else "#" for char in self.apiobject.name) + ".json"

    def __init__(self,
                 guild_id: int,
                 messages_to_send: List[Union[TextMESSAGE, VoiceMESSAGE]],
                 generate_log: bool=False):
        self._messages = messages_to_send
        super().__init__(guild_id, generate_log)

    async def add_message(self, message: Union[TextMESSAGE, VoiceMESSAGE]):
        """~  add_message  ~
        @Info:   Adds a message to the message list
        @Param:  message ~ message object to add
        """
        if not isinstance(message, (TextMESSAGE, VoiceMESSAGE)):
            trace(f"[GUILD]: Invalid xxxMESSAGE type: {type(message).__name__}, expected  {TextMESSAGE.__name__} or {VoiceMESSAGE.__name__}", TraceLEVELS.ERROR)
            return False

        if not await message.initialize():
            return False

        if isinstance(message, TextMESSAGE):
            self.t_messages.append(message)
        elif isinstance(message, VoiceMESSAGE):
            self.vc_messages.append(message)

        return True
    
    def remove_message(self, message: Union[TextMESSAGE, VoiceMESSAGE]):
        """~ remove_message ~
        @Info:   Removes a message from the message list
        @Param:  message ~ message object to remove
        """
        if isinstance(message, TextMESSAGE):
            self.t_messages.remove(message)
            return True
        elif isinstance(message, VoiceMESSAGE):
            self.vc_messages.remove(message)
            return True

        return False

    async def initialize(self) -> bool:
        """
        Name:   initialize
        Param:  void
        Return: bool:
                - Returns True if the initialization was successful
                - Returns False if failed, indicating the object should be removed from the server_list
        Info:   This function initializes the API related objects and then tries to initialize the MESSAGE objects.
        """
        if self.initialized: # Already initialized
            return True

        guild_id = self.snowflake
        cl = client.get_client()
        self.apiobject = cl.get_guild(guild_id)

        if self.apiobject is not None:
            for message in self._messages:
                await self.add_message(message)

            self.initialized = True
            return True

        trace(f"[GUILD]: Unable to find guild with ID: {guild_id}", TraceLEVELS.ERROR)
        return False

    async def advertise(self,
                        mode: Literal["text", "voice"]):
        """~ advertise ~
            @Info:
            This is the main coroutine that is responsible for sending all the messages to this specificc guild,
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
                if self._generate_log and message_ret is not None:
                    await self.generate_log(message_ret)

        # Cleanup messages marked for removal
        for message in marked_del:
            if message in msg_list:
                msg_list.remove(message)
            trace(f"[GUILD]: Removing a {type(message).__name__} because it's channels were removed, in guild {self.apiobject.name}(ID: {self.snowflake})")


@sql.register_type("GuildTYPE")
class USER(BaseGUILD):
    """~ USER ~
        @Info:
        The USER objects represents a Discord user/member.
        @Params:
        - user_id: int ~ id of the user you want to DM,
        - messages: list ~ list of DirectMESSAGE objects which
                           represent messages that will be sent to the DM
        - generate_log: bool ~ dictates if log should be generated for each sent message"""

    __logname__ = "USER"
    __slots__   = set()  # Removes __dict__ (prevents dynamic attributes)

    @property
    def log_file_name(self):
        """~ property (getter) ~
        @Info: The method returns a string that transforms the USER's discord name into
               a string that contains only allowed character. This is a method instead of
               property because the name can change overtime."""
        return "".join(char if char not in C_FILE_NAME_FORBIDDEN_CHAR else "#" for char in f"{self.apiobject.display_name}#{self.apiobject.discriminator}") + ".json"

    def __init__(self,
                 user_id: int,
                 messages_to_send: List[DirectMESSAGE],
                 generate_log: bool = False) -> None:
        super().__init__(user_id, generate_log)
        self._messages = messages_to_send

    async def add_message(self, message):
        """~  add_message  ~
        @Info:   Adds a message to the message list
        @Param:  message ~ message object to add
        """
        if not isinstance(message, DirectMESSAGE):
            trace(f"[USER]: Invalid xxxMESSAGE type: {type(message).__name__}, expected  {DirectMESSAGE.__name__}", TraceLEVELS.ERROR)
            return False
        if not await message.initialize(user=self.apiobject):
            return False
        self.t_messages.append(message)
        return True

    async def initialize(self) -> bool:
        """
        Name:   initialize
        Param:  void
        Return: bool:
                - Returns True if the initialization was successful
                - Returns False if failed, indicating the object should be removed from the server_list
        Info:   This function initializes the API related objects and then tries to initialize the MESSAGE objects.
        """
        if self.initialized: # Already initialized
            return True

        user_id = self.snowflake
        cl = client.get_client()
        self.apiobject = cl.get_user(user_id)
        if self.apiobject is None: # User not found in cache, try to fetch from API
            self.apiobject = await cl.fetch_user(user_id)

        if self.apiobject is not None:
            for message in self._messages:
                await self.add_message(message)
            
            self.initialized = True
            return True

        trace(f"[USER]: Unable to create DM with user id: {user_id}", TraceLEVELS.ERROR)
        return False

    async def advertise(self,
                        mode: Literal["text", "voice"]) -> None:
        """
            ~ advertise ~
            @Info:
            This is the main coroutine that is responsible for sending all the messages to this specificc guild,
            it is called from the core module's advertiser task"""
        if mode == "text":  # Does not have voice messages, only text based (DirectMESSAGE)
            for message in self.t_messages: # Copy the avoid issues with the list being modified while iterating
                if message.is_ready():
                    message.reset_timer()
                    message_ret = await message.send()
                    if self._generate_log and message_ret is not None:
                        await self.generate_log(message_ret)
                    
                    if message.dm_channel is None:
                        self.t_messages.clear()            # Remove all messages since that they all share the same user and will fail
                        trace(f"Removing all messages for user {self.apiobject.display_name}#{self.apiobject.discriminator} (ID: {self.snowflake}) because we do not have permissions to send to that user.", TraceLEVELS.WARNING)
                        break