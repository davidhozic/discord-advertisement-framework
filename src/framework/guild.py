from    .tracing import *
from    .const import *
from    .message import *
from    . import client
from    contextlib import suppress
from    typing import Union, List
import  time
import  os


__all__ = (
    "GUILD",
)

#######################################################################
# Globals
#######################################################################
m_server_log_output_path = None

class BaseGUILD:
    """ ~ BaseGUILD ~
        BaseGUILD object is used for creating inherited classes that work like a guild"""
    __slots__ = (
        "apiobject",
        "_generate_log",
        "log_file_name"
    )
    def __init__(self,
                 id: int,
                 generate_log: bool=False) -> None:
        self.apiobject = id
        self._generate_log = generate_log
    
    def get_log_guild_context(self, **options) -> str:
        raise NotImplementedError

    async def initialize(self) -> bool:
        raise NotImplementedError
    
    async def advertise(self,
                        attr_name: str=None):
        for message in getattr(self, attr_name):
            if message.is_ready():
                message_ret = await message.send()
                if self._generate_log and message_ret is not None:
                    self.generate_log(message_ret)
    
    def generate_log(self,
                     options) -> str:
        """
        Name:   generate_log
        Param:
            - data_context  - str representation of sent data, which is return data of xxxMESSAGE.send()
        Info:   Generates a log of a xxxxMESSAGE send attempt
        """
        data_context = options.pop("data_context")
        # Generate timestamp
        timestruct = time.localtime()
        timestamp = "{:02d}.{:02d}.{:04d} {:02d}:{:02d}".format(timestruct.tm_mday,
                                                                timestruct.tm_mon,
                                                                timestruct.tm_year,
                                                                timestruct.tm_hour,
                                                                timestruct.tm_min)
        guild_context = ""                                                                
        for x in self.get_log_guild_context(**options).splitlines():
            guild_context += f"\t{x}\n"
        guild_context = guild_context.rstrip()

        appender_data = f"""
# MESSAGE LOG:
{data_context}
***
## Other data:
-   ```
{guild_context}
    Timestamp: {timestamp}
    ```
***
<br><br><br>
"""
        # Write into file
        try:
            with suppress(FileExistsError):
                os.mkdir(m_server_log_output_path)
            with open(os.path.join(m_server_log_output_path, self.log_file_name),'a', encoding='utf-8') as appender:
                appender.write(appender_data)
        except OSError as os_exception:
            trace(f"Unable to save log. Exception: {os_exception}", TraceLEVELS.WARNING)


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
        "_generate_log",
        "log_file_name"
    )

    def __init__(self,
                 guild_id: int,
                 messages_to_send: List[Union[TextMESSAGE, VoiceMESSAGE]],
                 generate_log: bool=False):
        self.t_messages = []
        self.vc_messages = []
        for message in messages_to_send:
            if type(message) is TextMESSAGE:
                self.t_messages.append(message)
            elif type(message) is VoiceMESSAGE:
                self.vc_messages.append(message)
        return super().__init__(guild_id, generate_log)

    def get_log_guild_context(self,
                              **options) -> str:
        # Generate channel log
        succeeded_ch = options.pop("succeeded_ch")
        failed_ch = options.pop("failed_ch")
        succeeded_ch = "[\n" + "".join(f"\t\t{ch}(ID: {ch.id}),\n" for ch in succeeded_ch).rstrip(",\n") + "\n\t]" if len(succeeded_ch) else "[]"
        if len(failed_ch):
            tmp_chs, failed_ch = failed_ch, "["
            for ch in tmp_chs:
                ch_reason = str(ch["reason"]).replace("\n", "; ")
                failed_ch += f"\n\t\t{ch['channel']}(ID: {ch['channel'].id}) >>> [ {ch_reason} ],"
            failed_ch = failed_ch.rstrip(",") + "\n\t]"
        else:
            failed_ch = "[]"
        return \
f"""\
Guild: {self.apiobject.name}(ID: {self.apiobject.id})
Successful channels: {succeeded_ch}
Failed channels: {failed_ch}
"""

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
        guild_id = self.apiobject
        cl = client.get_client()
        self.apiobject = cl.get_guild(guild_id)

        if self.apiobject is not None:
        # Create a file name without the non allowed characters. Windows' list was choosen to generate the forbidden character because only forbids '/'
            self.log_file_name = "".join(char if char not in C_FILE_NAME_FORBIDDEN_CHAR else "#" for char in self.apiobject.name) + ".md"

            for message in self.t_messages[:]:
                """ Iterate thru the slice text messages list and initialize each
                    message object. If the message objects fails to initialize,
                    then it is removed from the original list."""
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