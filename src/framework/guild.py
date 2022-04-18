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
import  time
import  json
import pathlib

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
    __slots__ = (
        "apiobject",
        "_generate_log",
        "log_file_name",
        "t_messages",
        "vc_messages"
    )
    def __init__(self,
                 snowflake: int,
                 generate_log: bool=False) -> None:
        self.apiobject = snowflake
        self._generate_log = generate_log
        self.log_file_name = None
        self.t_messages = []
        self.vc_messages = []

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

    def generate_log(self,
                     **message_context) -> None:
        """
        Name:   generate_log
        Param:
            - data_context  - str representation of sent data, which is return data of xxxMESSAGE.send()
        Info:   Generates a log of a xxxxMESSAGE send attempt
        """
        # Generate timestamp
        timestruct = time.localtime()
        timestamp = "{:02d}.{:02d}.{:04d} {:02d}:{:02d}:{:02d}".format( timestruct.tm_mday,
                                                                        timestruct.tm_mon,
                                                                        timestruct.tm_year,
                                                                        timestruct.tm_hour,
                                                                        timestruct.tm_min,
                                                                        timestruct.tm_sec)

        logging_output = pathlib.Path(GLOBALS.server_log_path)\
                         .joinpath("{:02d}".format(timestruct.tm_year))\
                         .joinpath("{:02d}".format(timestruct.tm_mon))\
                         .joinpath("{:02d}".format(timestruct.tm_mday))

        # Write into file
        try:
            with suppress(FileExistsError):
                pathlib.Path(logging_output).mkdir(parents=True,exist_ok=True)

            logging_output = str(logging_output.joinpath(self.log_file_name))

            with suppress(FileExistsError):
                with open(logging_output,'x', encoding='utf-8'):
                    pass

            with open(logging_output,'r+', encoding='utf-8') as appender:
                appender_data = None

                try:
                    appender_data = json.load(appender)
                except json.JSONDecodeError:
                    appender_data = {}
                    appender_data["name"] = str(self.apiobject)
                    appender_data["id"] = self.apiobject.id
                    appender_data["type"] = type(self).__name__
                    appender_data["message_history"] = []
                finally:
                    with open(logging_output,'w', encoding='utf-8'):
                        pass
                    appender.seek(0)

                appender_data["message_history"].insert(0,
                    {
                        **message_context,
                        "index":    appender_data["message_history"][0]["index"] + 1 if len(appender_data["message_history"]) else 0,
                        "timestamp": timestamp
                    })
                json.dump(appender_data, appender, indent=4)

        except Exception as exception:
            trace(f"Unable to save log. Exception: {exception}", TraceLEVELS.WARNING)


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
    __slots__ = (
        "apiobject",
        "t_messages",
        "vc_messages",
        "__messages",
        "_generate_log",
        "log_file_name"
    )

    def __init__(self,
                 guild_id: int,
                 messages_to_send: List[Union[TextMESSAGE, VoiceMESSAGE]],
                 generate_log: bool=False):
        self.__messages = messages_to_send
        super().__init__(guild_id, generate_log)

    async def initialize(self) -> bool:
        """
        Name:   initialize
        Param:  void
        Return: bool:
                - Returns True if the initialization was successful
                - Returns False if failed, indicating the object should be removed from the server_list
        Info:   The function initializes all the GUILD objects (and other objects inside the GUILD object reccurssively).
                It tries to get the discord.Guild object from the self.guild id and then tries to initialize the MESSAGE objects.
        """
        for message in self.__messages:
            if type(message) is TextMESSAGE:
                self.t_messages.append(message)
            elif type(message) is VoiceMESSAGE:
                self.vc_messages.append(message)
            else:
                trace(f"Invalid xxxMESSAGE type: {type(message).__name__}, expected  {TextMESSAGE.__name__} or {VoiceMESSAGE.__name__}", TraceLEVELS.ERROR)
        del self.__messages

        guild_id = self.apiobject
        cl = client.get_client()
        self.apiobject = cl.get_guild(guild_id)

        if self.apiobject is not None:
        # Create a file name without the non allowed characters. Windows' list was choosen to generate the forbidden character because only forbids '/'
            self.log_file_name = "".join(char if char not in C_FILE_NAME_FORBIDDEN_CHAR else "#" for char in self.apiobject.name) + ".json"

            for message in self.t_messages[:]:
                # Iterate thru the slice text messages list and initialize each
                # message object. If the message objects fails to initialize,
                # then it is removed from the original list.
                if not await message.initialize():
                    self.t_messages.remove(message)

            for message in self.vc_messages[:]:
                # Same as above but for voice messages
                if not await message.initialize():
                    self.vc_messages.remove(message)

            if not len(self.t_messages) + len(self.vc_messages):
                return False

            return True

        return False

    async def advertise(self,
                        mode: Literal["text", "voice"]):
        """
            ~ advertise ~
            @Info:
            This is the main coroutine that is responsible for sending all the messages to this specificc guild,
            it is called from the core module's advertiser task
        """
        for message in self.t_messages if mode == "text" else self.vc_messages:
            if message.is_ready():
                message_ret = await message.send()
                # Check if the message still has any channels (as they can be auto removed on 404 status)
                if not len(message.channels):
                    # Remove message from the list if it has not channels left
                    getattr(self, "t_messages" if mode == "text" else "vc_messages").remove(message)
                    trace(f"Removing a {type(message).__name__} because it's channels were removed, in guild {self.apiobject.name}(ID: {self.apiobject.id})")

                if self._generate_log and message_ret is not None:
                    self.generate_log(**message_ret)


class USER(BaseGUILD):
    """~ USER ~
        @Info:
        The USER objects represents a Discord user/member.
        @Params:
        - user_id: int ~ id of the user you want to DM,
        - messages: list ~ list of DirectMESSAGE objects which
                           represent messages that will be sent to the DM
        - generate_log: bool ~ dictates if log should be generated for each sent message"""
    __slots__ = (
        "apiobject",
        "_generate_log",
        "t_messages",
        "vc_messages",
        "__messages",
        "log_file_name",
    )
    def __init__(self,
                 user_id: int,
                 messages_to_send: List[DirectMESSAGE],
                 generate_log: bool = False) -> None:
        super().__init__(user_id, generate_log)
        self.__messages = messages_to_send

    async def initialize(self) -> bool:
        for message in self.__messages:
            if type(message) is DirectMESSAGE:
                self.t_messages.append(message)
            else:
                trace(f"Invalid xxxMESSAGE type: {type(message).__name__}, expected  {DirectMESSAGE.__name__}", TraceLEVELS.ERROR)
        del self.__messages

        user_id = self.apiobject
        cl = client.get_client()
        self.apiobject = cl.get_user(user_id)

        if self.apiobject is not None:
            self.log_file_name = "".join(char if char not in C_FILE_NAME_FORBIDDEN_CHAR else "#" for char in f"{self.apiobject.display_name}#{self.apiobject.discriminator}") + ".json"
            for message in self.t_messages[:]:
                if (type(message) is not DirectMESSAGE or
                    not await message.initialize(user_id=user_id)
                ):
                    self.t_messages.remove(message)
            if not len(self.t_messages):
                return False
            return True

        trace(f"Unable to create DM with user id: {user_id}", TraceLEVELS.ERROR)
        return False

    async def advertise(self,
                        mode: Literal["text", "voice"]):
        """
            ~ advertise ~
            @Info:
            This is the main coroutine that is responsible for sending all the messages to this specificc guild,
            it is called from the core module's advertiser task
        """
        for message in self.t_messages if mode == "text" else self.vc_messages:
            if message.is_ready():
                message_ret = await message.send()
                if self._generate_log and message_ret is not None:
                    self.generate_log(**message_ret)
