"""
    DISCORD ADVERTISEMENT FRAMEWORK (DSF)
    Author      :: David Hozic
    Copyright   :: Copyright (c) 2022 David Hozic
    Version     :: V1.7.6.2
"""
from    contextlib import suppress
from    typing import Literal, Union, List
from    enum import Enum, auto
from    functools import singledispatchmethod
import  time
import  asyncio
import  random
import  os
import  _discord as discord
import  datetime
import  copy


# TODO: Documentation, make VoiceMESSAGE work, move generate log into message classess

#######################################################################
# Exports
#######################################################################
__all__ = (    # __all__ variable dictates which objects get imported when using from <module> import *
    "discord",
    "C_DAY_TO_SECOND",
    "C_HOUR_TO_SECOND",
    "C_MINUTE_TO_SECOND",
    "GUILD",
    "TextMESSAGE",
    "VoiceMESSAGE",
    "FILE",
    "EMBED",
    "EmbedFIELD",
    "run",
    "data_function",
    "get_client",
    "shutdown"
)

#######################################################################
# Globals   (These are all set in the framework.run function)
#######################################################################
m_user_callback          = None     # User provided function to call after framework is ready
m_server_log_output_path = None     # User provided for server log output path
m_server_list            = None     # User provided server list
m_debug                  = None     # User provided option to enable debugging
m_client                 = None     # Pycord Client object

#######################################################################
# Contants
#######################################################################
C_DAY_TO_SECOND = 86400
C_HOUR_TO_SECOND= 3600
C_MINUTE_TO_SECOND = 60

C_RT_AVOID_DELAY   = 1.5        # Rate limit avoidance delay
C_TASK_SLEEP_DELAY = 0.1        # Advertiser task sleep
#######################################################################
# Debugging
#######################################################################
class TraceLEVELS(Enum):
    """
    Info: Level of trace for debug
    """
    NORMAL = 0
    WARNING = auto()
    ERROR =  auto()

def trace(message: str,
          level:   TraceLEVELS = TraceLEVELS.NORMAL):
    """"
    Name : trace
    Param:
    - message : str          = Trace message
    - level   : TraceLEVELS = Level of the trace
    """
    if m_debug:
        l_timestruct = time.localtime()
        l_timestamp = "Date: {:02d}.{:02d}.{:04d} Time:{:02d}:{:02d}"
        l_timestamp = l_timestamp.format(l_timestruct.tm_mday,
                                         l_timestruct.tm_mon,
                                         l_timestruct.tm_year,
                                         l_timestruct.tm_hour,
                                         l_timestruct.tm_min)
        l_trace = f"{l_timestamp}\nTrace level: {level.name}\nMessage: {message}\n"
        print(l_trace)


#######################################################################
# Decorators
#######################################################################
class FunctionBaseCLASS:
    """
    type: dummy class
    name: FunctionBaseCLASS
    info: used as a base class to FunctionCLASS which gets created in framework.data_function decorator.
    Because the FunctionCLASS is inaccessible outside the data_function decorator, this class is used to detect
    if the MESSAGE.data parameter is of function type, because the function isinstance also returns True when comparing
    the object to it's class or to the base class from which the object class is inherited from.
    """

def data_function(fnc):
    """
    type:   Decorator
    name:   data_function
    info:   Decorator used to create a framework FunctionCLASS class for function
    return: FunctionCLASS
    """
    class FunctionCLASS(FunctionBaseCLASS):
        """"
        _FUNCTION_CLS_
        Info : Used for creating special classes that are then used to create objects in the framework.MESSAGE
               data parameter, allows for sending dynamic contentent received thru an user defined function.

        Param: function
        """
        __slots__ = (
            "args",
            "kwargs",
            "func_name",
        )

        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs
            self.func_name = fnc.__name__

        def get_data(self):
            """
            Retreives the data from the user function
            """
            return fnc(*self.args, **self.kwargs)
    return FunctionCLASS

#######################################################################
# Misc. classes
#######################################################################
class TIMER:
    """
    TIMER
    Info : Used in MESSAGE objects as a send timer
    """
    __slots__ = (
        "running",
        "startms"
    )

    def __init__(self):
        "Initiate the timer"
        self.running = False
        self.startms = 0
    def start(self):
        "Start the timer"
        if self.running:
            return True
        self.running = True
        self.startms = time.time()
        return False
    def elapsed(self):
        "Return the timer elapsed from last reset"
        return time.time() - self.startms if self.running else 0
    def reset (self):
        "Reset the timer"
        self.running = False

#######################################################################
# Framework classes
#######################################################################
class CLIENT(discord.Client):
    """
        Name : CLIENT
        Info : Inherited class from discord.Client.
               Contains an additional on_ready function.
    """
    async def on_ready(self) -> None:
        """
        Name : on_ready
        Info : Tasks that is started by pycord when you have been successfully logged into discord.
        """
        trace(f"Logged in as {self.user}", TraceLEVELS.NORMAL)

        if initialize():
            # Initialization was successful, so create the advertiser task and start advertising.
            trace("Successful initialization!",TraceLEVELS.NORMAL)
            asyncio.gather(asyncio.create_task(advertiser()))
        else:
            # Initialization failed, close everything
            await shutdown()

        if m_user_callback:   # If user callback function was specified
            m_user_callback() # Call user provided function after framework has started



class EmbedFIELD:
    """
    Embedded field class for use in EMBED object constructor
    Parameters:
    -  Name         : str    -- Name of the field
    -  Content      : str    -- Content of the embedded field
    -  Inline       : bool   -- Make this field appear in the same line as the previous field
    """
    def __init__(self,
                 name : str,
                 content : str,
                 inline : bool=False):
        self.name = name
        self.content = content
        self.inline = inline

    def __iter__(self):
        """
        Name: __iter__
        Info: Iterator used to return EmbedFieldITER
        """
        class EmbedFieldITER:
            """
            Name: EmbedFieldITER
            Info: Iterator used to expand the EmbedFIELD object into name, content, inline
            """
            def __init__(self, data):
                self.__data = data
                self.__index = 0
                self.__max = len(data)
            def __next__(self):
                if self.__index == self.__max:
                    raise StopIteration
                self.__index +=1
                return self.__data[self.__index-1]
        return EmbedFieldITER([self.name, self.content, self.inline])


class EMBED(discord.Embed):
    """
    Derrived class of discord.Embed with easier definition
    Parameters:
        Added parameters:
            - author_name       : str           -- Name of embed author
            - author_icon       : str           -- Url to author image
            - image             : str           -- Url of image to be placed at the end of the embed
            - thumbnail         : str           -- Url of image that will be placed at the top right of embed
            - fields            : list          -- List of EmbedFIELD objects
        Inherited from discord.Embed:
            - For the other, original params see https://docs.pycord.dev/en/master/api.html?highlight=discord%20embed#discord.Embed

    """
    __slots__ = (
        'title',
        'url',
        'type',
        '_timestamp',
        '_colour',
        '_footer',
        '_image',
        '_thumbnail',
        '_video',
        '_provider',
        '_author',
        '_fields',
        'description',
    )
    # Static members
    Color = Colour = discord.Color  # Used for color parameter
    EmptyEmbed = discord.embeds.EmptyEmbed

    @staticmethod
    def from_discord_embed(_object : discord.Embed):
        """
        Name:   from_discord_embed
        Type:   static method
        Param:
            - object : discord.Embed | discord.Embed (same type) -- The discord Embed object you want converted into the framework.EMBED class
        """

        ret = EMBED()
        # Copy attributes but not special methods to the new EMBED. "dir" is used instead of "vars" because the object does not support the function.
        for key in dir(_object):
            if not key.startswith("__") and not key.endswith("__"):
                with suppress(AttributeError,TypeError):
                    if not callable(getattr(_object, key)) and not isinstance(getattr(_object.__class__, key), property):
                        setattr(ret, key, copy.deepcopy(getattr(_object,key)))


        return ret

    # Object members
    def __init__(self, *,
                # Additional parameters
                author_name: str=None,
                author_icon: str=EmptyEmbed,
                image: str= None,
                thumbnail : str = None,
                fields : List[EmbedFIELD] = None,
                # Base class parameters
                colour: Union[int, Colour] = EmptyEmbed,
                color: Union[int, Colour] = EmptyEmbed,
                title: str = EmptyEmbed,
                type :str = "rich",
                url: str= EmptyEmbed,
                description = EmptyEmbed,
                timestamp: datetime.datetime = None):

        ## Initiate original arguments from discord. Embed
        ## by looping thru the super().__init__ annotations(variables the function accepts)
        base_args = {}
        localargs = locals()
        for key in super().__init__.__annotations__:
            base_args[key] = localargs[key]
        super().__init__(**base_args)

        ## Set author
        if author_name is not None:
            self.set_author(name=author_name, icon_url=author_icon)
        ## Set image
        if image is not None:
            self.set_image(url=image)
        ## Set thumbnail
        if thumbnail is not None:
            self.set_thumbnail(url=thumbnail)
        ### Set fields
        if fields is not None:
            for field_name, content, inline in fields:
                self.add_field(name=field_name,value=content,inline=inline)


class FILE:
    """
    Name: FILE
    Info: FILE object used as a data parameter to the MESSAGE objects.
          This is needed aposed to a normal file object because this way,
          you can edit the file after the framework has already been started.
    """
    __slots__ = ("filename",)
    def __init__(self,
                 filename):
        self.filename = filename
        # Try to open file before framework starts for easier exception debug
        with open(filename, "rb") as reader:
            pass


class AUDIO:
    """
    Name: AUDIO
    Info: Represents an audio parameter that is used in the VoiceMESSAGE data parameterer
    """
    __slots__ = ("filename",)
    def __init__(self,
                 filename):
        self.filename = filename
        # Try to open file before framework starts for easier exception debug
        with open(filename, "rb") as reader:
            pass


class BaseMESSAGE:
    __slots__ = (
        "randomized_time",
        "period",
        "random_range",
        "channels",
        "timer",
        "force_retry",
        "sent_messages"
    )
    def __init__(self,
                start_period : Union[float,None],
                end_period : float,
                channel_ids : List[int],
                start_now : bool=True):

        if start_period is None:            # If start_period is none -> period will not be randomized
            self.randomized_time = False
            self.period = end_period
        else:
            self.randomized_time = True
            self.random_range = (start_period, end_period)
            self.period = random.randrange(*self.random_range)  # This will happen after each sending as well

        self.channels = channel_ids
        self.timer = TIMER()
        self.force_retry = {"ENABLED" : start_now, "TIME" : 0}
        self.sent_messages = {ch_id : None for ch_id in channel_ids}


class VoiceMESSAGE(BaseMESSAGE):
    """
    Name: VoiceMESSAGE
    Info: The VoiceMESSAGE object containts parameters which describe behaviour and data that will be sent to the channels.
    Params:
    - Start Period , End Period (start_period, end_period) - These 2 parameters specify the period on which the messages will be sent:
    Start Period can be either:
        - None - Messages will be sent on intervals specified by End period,
        - Integer >= 0 - Messages will be sent on intervals randomly chosen between Start period and End period,
          where the randomly chosen intervals will be re-randomized after each sent message.
    - Data (data) - The data parameter is the actual data that will be sent using discord's API. The data types of this parameter can be:
        - Path to an audio file (str)
        - Function that accepts any amount of parameters and returns any of the above types.
          To pass a function, YOU MUST USE THE framework.data_function decorator on the function before passing the function to the framework.
    - Channel IDs (channel_ids) - List of IDs of all the channels you want data to be sent into.
    - Start Now (start_now) - A bool variable that can be either True or False. If True, then the framework will send the message
      as soon as it is run and then wait it's period before trying again. If False, then the message will not be sent immediatly after framework is ready,
      but will instead wait for the period to elapse.
    """
    __slots__ = (
        "randomized_time",
        "period",
        "random_range",
        "data",
        "channels",
        "timer",
    )
    def __init__(self, start_period: Union[float, None],
                 end_period: float,
                 data: AUDIO,
                 channel_ids: List[int],
                 start_now: bool = True):
        super().__init__(start_period, end_period, channel_ids, start_now)
        self.data = data


class TextMESSAGE(BaseMESSAGE):
    """
    Name: TextMESSAGE
    Info: The TextMESSAGE object containts parameters which describe behaviour and data that will be sent to the channels.
    Params:
    - Start Period , End Period (start_period, end_period) - These 2 parameters specify the period on which the messages will be sent:
    Start Period can be either:
        - None - Messages will be sent on intervals specified by End period,
        - Integer >= 0 - Messages will be sent on intervals randomly chosen between Start period and End period,
          where the randomly chosen intervals will be re-randomized after each sent message.
    - Data (data) - The data parameter is the actual data that will be sent using discord's API. The data types of this parameter can be:
        - String (normal text),
        - framework.EMBED,
        - framework.FILE,
        - List/Tuple containing any of the above arguments (There can up to 1 string, up to 1 embed and up to 10 framework.FILE objects,
          if more than 1 string or embeds are sent, the framework will only consider the last found).
        - Function that accepts any amount of parameters and returns any of the above types.
          To pass a function, YOU MUST USE THE framework.data_function decorator on the function before passing the function to the framework.
    - Channel IDs (channel_ids) - List of IDs of all the channels you want data to be sent into.
    - Send mode (mode) - Parameter that defines how message will be sent to a channel. It can be "send" - each period a new message will be sent,
                        "edit" - each period the previously send message will be edited (if it exists) or "clear-send" - previous message will be deleted and
                        a new one sent.
    - Start Now (start_now) - A bool variable that can be either True or False. If True, then the framework will send the message
      as soon as it is run and then wait it's period before trying again. If False, then the message will not be sent immediatly after framework is ready,
      but will instead wait for the period to elapse.
    """
    __slots__ = (
        "randomized_time",
        "period",
        "random_range",
        "data",
        "channels",
        "timer",
        "mode",
        "force_retry",
        "sent_messages"
    )
    def __init__(self, start_period: Union[float, None],
                 end_period: float,
                 data: Union[str, EMBED, FILE,List[Union[str, EMBED, FILE]]],
                 channel_ids: List[int],
                 mode: Literal["send", "edit", "clear-send"] = "send",
                 start_now: bool = True):
        super().__init__(start_period, end_period, channel_ids, start_now)
        self.data = data
        self.mode = mode

    async def send_to_channels(self):
        if self.timer.start() and (not self.force_retry["ENABLED"] and self.timer.elapsed() > self.period or self.force_retry["ENABLED"] and self.timer.elapsed() > self.force_retry["TIME"]):
            self.timer.reset()
            self.timer.start()
            self.force_retry["ENABLED"] = False
            if self.randomized_time is True:           # If first parameter to msg object is not None
                self.period = random.randrange(*self.random_range)

            # Parse data from the data parameter
            l_data_to_send  = None
            if isinstance(self.data, FunctionBaseCLASS):
                l_data_to_send = self.data.get_data()
            else:
                l_data_to_send = self.data

            l_embed_to_send = None
            l_text_to_send  = None
            l_files_to_send  = []
            if l_data_to_send is not None:
                if not isinstance(l_data_to_send, (list, tuple, set)):
                    """ Put into a list for easier iteration.
                        Technically only necessary if self.data  is a function (dynamic return),
                        since normal (str, EMBED, FILE) get pre-checked in initialization."""
                    l_data_to_send = (l_data_to_send,)

                for element in l_data_to_send:
                    if isinstance(element, str):
                        l_text_to_send = element
                    elif isinstance(element, EMBED):
                        l_embed_to_send = element
                    elif isinstance(element, FILE):
                        l_files_to_send.append(element)

            # Send messages
            if l_text_to_send is not None or l_embed_to_send is not None or len(l_files_to_send) > 0:
                l_errored_channels = []
                l_succeded_channels= []

                # Send to channels
                for l_channel in self.channels:
                    # Clear previous messages sent to channel if mode is MODE_DELETE_SEND
                    if self.mode == "clear-send" and self.sent_messages[l_channel.id] is not None:
                        for tries in range(3):
                            try:
                                # Delete discord message that originated from this MESSAGE object
                                await self.sent_messages[l_channel.id].delete()
                                self.sent_messages[l_channel.id] = None
                                break
                            except discord.HTTPException as ex:
                                if ex.status == 429:
                                    await asyncio.sleep(int(ex.response.headers["Retry-After"])  + 1)

                    # Send/Edit messages
                    for tries in range(3):  # Maximum 3 tries (if rate limit)
                        try:
                            # Mode dictates to send new message or delete previous and then send new message or mode dictates edit but message was  never sent to this channel before
                            with l_channel.typing():
                                # Rate limit avoidance
                                await asyncio.sleep(C_RT_AVOID_DELAY)

                                if  self.mode in  {"send" , "clear-send"} or\
                                    self.mode == "edit" and self.sent_messages[l_channel.id] is None:
                                    l_discord_sent_msg = await l_channel.send(l_text_to_send,
                                                                            embed=l_embed_to_send,
                                                                            # Create discord.File objects here so it is catched by the except block and then logged
                                                                            files=[discord.File(fwFILE.filename) for fwFILE in l_files_to_send])

                                    self.sent_messages[l_channel.id] = l_discord_sent_msg

                                # Mode is edit and message was already send to this channel
                                elif self.mode == "edit":
                                    await self.sent_messages[l_channel.id].edit (l_text_to_send,
                                                                            embed=l_embed_to_send)

                            l_succeded_channels.append(l_channel)
                            break    # Break out of the tries loop

                        except Exception as ex:
                            # Failed to send message
                            if isinstance(ex, discord.HTTPException):
                                if ex.status == 429:    # Rate limit
                                    retry_after = int(ex.response.headers["Retry-After"])  + 1
                                    if ex.code == 20026:    # Slow Mode
                                        self.force_retry["ENABLED"] = True
                                        self.force_retry["TIME"] = retry_after
                                    else:   # Normal (write) rate limit
                                        # Rate limit but not slow mode -> put the framework to sleep as it won't be able to send any messages globaly
                                        await asyncio.sleep(retry_after)

                            # Immediate exit conditions
                            # Since python has short circuit evaluation, nothing is wrong with using ex.status and ex.code
                            if (not isinstance(ex, discord.HTTPException) or\
                                ex.status != 429 or\
                                ex.code == 20026
                            ):
                                l_errored_channels.append({"channel":l_channel, "reason":ex})
                                break

            # Return sent data + failed and successful function for logging purposes
            return l_text_to_send, l_embed_to_send, l_files_to_send, l_succeded_channels, l_errored_channels

class GUILD:
    """
    Name: GUILD
    Info: The GUILD object represents a server to which messages will be sent.
    Params:
    - Guild ID - identificator which can be obtained by enabling developer mode in discord's settings and
                 afterwards right-clicking on the server/guild icon in the server list and clicking "Copy ID",
    - List of MESSAGE objects - Python list or tuple contating MESSAGE objects.
    - Generate file log - bool variable, if True it will generate a file log for each message send attempt.
    """
    __slots__ = (
        "guild",
        "messages",
        "_generate_log",
        "guild_file_name"
    )

    def __init__(self,
                 guild_id : int,
                 messages_to_send : List[Union[TextMESSAGE, VoiceMESSAGE]],
                 generate_log : bool = False):

        self.guild =    guild_id
        self.messages = messages_to_send
        self._generate_log = generate_log
        self.guild_file_name = None

    @singledispatchmethod
    def generate_log(self,
                      sent_text : str,
                      sent_embed : discord.Embed,
                      sent_files : list,
                      succeeded_ch : list,
                      failed_ch : list) -> str:
        """
        Name: generate_log
        Info: Generates a log of a message send attempt
        """
        # Generate text
        if sent_text is not None:
            tmp_text , sent_text = sent_text, ""
            sent_text += "- ```\n"
            for line in tmp_text.splitlines():
                sent_text += f"  {line}\n"
            sent_text += "  ```"
        else:
            sent_text = ""

        #Generate embed
        EmptyEmbed = discord.embeds._EmptyEmbed

        if sent_embed is not None:
            tmp_emb = sent_embed
            ets = sent_embed.timestamp
            sent_embed = \
f"""
Title:  {tmp_emb.title if type(tmp_emb.title) is not EmptyEmbed else ""}

Author:  {tmp_emb.author.name if type(tmp_emb.author.name) is not EmptyEmbed else ""}

Thumbnail:  {tmp_emb.thumbnail.url if type(tmp_emb.thumbnail.url) is not EmptyEmbed else ""}

Image:  {tmp_emb.image.url if type(tmp_emb.image.url) is not EmptyEmbed else ""}

Description:  {tmp_emb.description if type(tmp_emb.description) is not EmptyEmbed else ""}

Color:  {tmp_emb.colour if type(tmp_emb.colour) is not EmptyEmbed else ""}

Timestamp:  {f"{ets.day}.{ets.month}.{ets.year}  {ets.hour}:{ets.minute}:{ets.second}" if type(ets) is not EmptyEmbed else ""}
"""
            sent_embed += "\nFields:"
            for field in tmp_emb.fields:
                sent_embed += f"\n - {field.name}\n"
                sent_embed += "\t```\n"
                for line in field.value.splitlines():
                    sent_embed += f"\t{line}\n"
                sent_embed += "\t```"

        else:
            sent_embed = ""

        # Generate timestamp
        l_timestruct = time.localtime()
        l_timestamp = "{:02d}.{:02d}.{:04d} {:02d}:{:02d}".format(l_timestruct.tm_mday,
                                                                  l_timestruct.tm_mon,
                                                                  l_timestruct.tm_year,
                                                                  l_timestruct.tm_hour,
                                                                  l_timestruct.tm_min)
        # Generate channel log
        succeeded_ch = "[\n" + "".join(f"\t\t{ch.name}(ID: {ch.id}),\n" for ch in succeeded_ch).rstrip(",\n") + "\n\t]" if len(succeeded_ch) else "[]"
        if len(failed_ch):
            tmp_chs, failed_ch = failed_ch, "["
            for ch in tmp_chs:
                ch_reason = str(ch["reason"]).replace("\n", "; ")
                failed_ch += f"\n\t\t{ch['channel'].name}(ID: {ch['channel'].id}) >>> [ {ch_reason} ],"
            failed_ch = failed_ch.rstrip(",") + "\n\t]"
        else:
            failed_ch = "[]"

        # Generate files
        sent_files = "".join(    f"- ```\n  {file.filename}\n  ```\n" for file in sent_files    ).rstrip("\n")

        return f'''
# MESSAGE LOG:
## Text:
{sent_text}
***
## Embed:
{sent_embed}
***
## Files:
{sent_files}
***
## Other data:
-   ```
    Server: {self.guild.name}
    Succeeded in channels: {succeeded_ch}
    Failed in channels: {failed_ch}
    Timestamp: {l_timestamp}
    ```
***
<br><br><br>
'''

    @generate_log.register
    def overload_generate_log(self,
                      send_audio   : AUDIO,
                      succeeded_ch : list,
                      failed_ch : list) -> str:
        """
        Name: generate_log (for VoiceMessages)
        Info: Generates a log of a message send attempt,
              that is overloaded to accept audio
        """

        # Generate timestamp
        l_timestruct = time.localtime()
        l_timestamp = "{:02d}.{:02d}.{:04d} {:02d}:{:02d}".format(l_timestruct.tm_mday,
                                                                  l_timestruct.tm_mon,
                                                                  l_timestruct.tm_year,
                                                                  l_timestruct.tm_hour,
                                                                  l_timestruct.tm_min)
        # Generate channel log
        succeeded_ch = "[\n" + "".join(f"\t\t{ch.name}(ID: {ch.id}),\n" for ch in succeeded_ch).rstrip(",\n") + "\n\t]" if len(succeeded_ch) else "[]"
        if len(failed_ch):
            tmp_chs, failed_ch = failed_ch, "["
            for ch in tmp_chs:
                ch_reason = str(ch["reason"]).replace("\n", "; ")
                failed_ch += f"\n\t\t{ch['channel'].name}(ID: {ch['channel'].id}) >>> [ {ch_reason} ],"
            failed_ch = failed_ch.rstrip(",") + "\n\t]"
        else:
            failed_ch = "[]"


        return f'''
# MESSAGE LOG:
## Audio:
{send_audio}
***
## Other data:
-   ```
    Server: {self.guild.name}
    Succeeded in channels: {succeeded_ch}
    Failed in channels: {failed_ch}
    Timestamp: {l_timestamp}
    ```
***
<br><br><br>
'''

#######################################################################
# Tasks
#######################################################################
async def advertiser() -> None:
    """
    Name  : advertiser
    Param : void
    Info  : Main task that is responsible for the framework
    """
    while True:
        await asyncio.sleep(C_TASK_SLEEP_DELAY)
        for l_server in m_server_list[:]:
            """The list is sliced first to allow removal of guilds mid iteration
            in case all the message objects were deleted due to unrecoverable error"""
            l_trace = ""
            for l_msg in l_server.messages[:]:
                """The list is sliced first to allow removal mid iteration in case all the discord
                channels were deleted and the message objects needs to be deleted to avoid generation of empty logs"""
                l_msg_ret = await l_msg.send_to_channels()
                if l_msg_ret is not None:
                    l_trace += l_server.generate_log(*l_msg_ret)     # Generate trace of sent file
            # Save into file
            if l_server._generate_log and l_trace:
                with suppress(FileExistsError):
                    os.mkdir(m_server_log_output_path)
                with open(os.path.join(m_server_log_output_path, l_server.guild_file_name),'a', encoding='utf-8') as l_logfile:
                    l_logfile.write(l_trace)


#######################################################################
# Functions
#######################################################################
def initialize() -> bool:
    """
    Name: initialize
    Parameters: void
    Return: success: bool
    Info: Function that initializes the guild objects and then returns True on success or False on failure.
    """
    for l_server in m_server_list[:]:
        """
        Replace the guild IDs with actual discord.Guild objects or remove if any errors were discovered.
        The m_server_list is sliced (shallow copied) to allow item
        removal from the list while still under the for loop (the iterator will
        return items from the copied list by reference and I remove them from original list).
        """
        l_guild_id = l_server.guild
        l_server.guild = m_client.get_guild(l_guild_id)

        if l_server.guild is not None:
        # Create a file name without the non allowed characters. Windows' list was choosen to generate the forbidden character because only forbids '/'
            l_forbidden_file_names = ('<','>','"','/','\\','|','?','*',":")
            l_server.guild_file_name = "".join(char if char not in l_forbidden_file_names else "#" for char in l_server.guild.name) + ".md"

            for l_msg in l_server.messages[:]:
                """
                Initialize all the MESSAGE objects -- Replace all the channel IDs with actual channel objects.
                Slice (shallow copy) the messages array to allow removal of message objects without affecting the iterator.
                """

                # Remove duplicated channel ids
                for l_channel_id in l_msg.channels[:]:
                    if l_msg.channels.count(l_channel_id) > 1:
                        trace(f"Guild \"{l_server.guild.name}\" (ID: {l_guild_id}) has duplicated channel (ID: {l_channel_id})", TraceLEVELS.WARNING)
                        l_msg.channels.remove(l_channel_id)
                # Transform channel ids into pycord channel objects
                l_channel_i = 0
                while l_channel_i < len(l_msg.channels):
                    """
                    Replace the channel IDs with channel objects.
                    while loop is used as I don't want the index to increase every iteration
                    """
                    l_channel_id = l_msg.channels[l_channel_i]
                    l_msg.channels[l_channel_i] = m_client.get_channel(l_channel_id)
                    l_channel = l_msg.channels[l_channel_i]

                    if l_channel is None:
                        # Unable to find the channel objects, ergo remove.
                        trace(f"Unable to get channel from id: {l_channel_id} (Does not exist - Incorrect ID?) in GUILD: \"{l_server.guild.name}\" (ID: {l_guild_id})", TraceLEVELS.WARNING)
                        l_msg.channels.remove(l_channel)

                    elif l_channel.guild.id != l_guild_id:
                        # The channel is not part of this guild, ergo remove.
                        trace(f"Guild \"{l_server.guild.name}\" (ID: {l_guild_id}) has no channel \"{l_channel.name}\" (ID: {l_channel_id})", TraceLEVELS.WARNING)
                        l_msg.channels.remove(l_channel)
                    else:
                        l_channel_i += 1

                # Check for correct data types of the MESSAGE.data parameter
                if not isinstance(l_msg.data, FunctionBaseCLASS):
                    """
                    This is meant only as a pre-check if the parameters are correct so you wouldn't eg. start
                    sending this message 6 hours later and only then realize the parameters were incorrect.
                    The parameters also get checked/parsed each period right before the send.
                    """
                    # Convert any arguments passed into a list of arguments
                    if  isinstance(l_msg.data, (list, tuple, set)):
                        l_msg.data = list(l_msg.data)   # Convert into a regular list to allow removal of items
                    else:
                        l_msg.data = [l_msg.data]       # Place into a list for iteration, to avoid additional code

                    # Check all the arguments
                    for l_data in l_msg.data[:]:
                        """
                        Check all the data types of all the passed to the data parameter.
                        If class does not match the allowed types, then the object is removed.
                        The for loop iterates thru a shallow copy (sliced list) of l_data_params to allow removal of items
                        without affecting the iteration (would skip elements without a copy or use of while loop)
                        """
                        if (
                            not isinstance(l_data, str) and\
                            not isinstance(l_data, EMBED) and\
                            not isinstance(l_data, FILE)\
                        ):
                            if isinstance(l_data, FunctionBaseCLASS):
                                trace(f"The function can only be used on the data parameter directly, not in a list\nFunction: {l_data.func_name}", TraceLEVELS.ERROR)
                                l_msg.data.clear()
                                break
                            else:
                                trace(f"INVALID DATA PARAMETER PASSED!\nArgument is of type : {type(l_data).__name__}\nSee README.md for allowed data types\nGUILD: {l_server.guild.name} (ID: {l_server.guild.id})", TraceLEVELS.WARNING)
                                l_msg.data.remove(l_data)

                # Check if any data params are left and remove the message object if not
                if (not len(l_msg.channels) or
                    not isinstance(l_msg.data, FunctionBaseCLASS) and not len(l_msg.data)   # if isinstance FunctionBaseCLASS, then it has no len, and because of short-circuit, len will not be read
                ):
                    """
                    Failed parsing of all the channels
                    or/and all the data parameters inside the message object, ergo remove the message.
                    """
                    l_server.messages.remove(l_msg)

            if not len(l_server.messages):
                """
                No messages were successfuly processed,
                ergo remove the guild object from the list as it is useless.
                Trace is silent since it is already made in the deepest level of these checks.
                """
                m_server_list.remove(l_server)

        else:
            trace(f"Unable to create server object from server id: {l_guild_id}\nRemoving the object from the list!", TraceLEVELS.WARNING)
            m_server_list.remove(l_server)

    if len(m_server_list):
        return True
    else:
        trace("No guilds could be parsed", TraceLEVELS.ERROR)
        return False

async def shutdown() -> None:
    # TODO : Documentation
    """
    Name:   shutdown
    Params: void
    Return: None
    Info:   Stops the framework
    """
    await m_client.close()

def get_client()  -> CLIENT:
    """
    Name:   get_client
    Params: void
    Return: discord.Client | None
    Info:   Returns the client object used by the framework, so the user wouldn't have to run 2 clients.
    """
    return m_client


def run(token : str,
        server_list : List[GUILD],
        is_user : bool =False,
        user_callback : bool=None,
        server_log_output : str ="History",
        debug : bool=True) -> None:
    """
    @type  : function
    @name  : run
    @params:
        - token             : str       = access token for account
        - server_list       : list      = List of framework.GUILD objects
        - is_user           : bool      = Set to True if token is from an user account and not a bot account
        - user_callback     : function  = User callback function (gets called after framework is ran)
        - server_log_output : str       = Path where the server log files will be created
        - debug             : bool      = Print trace message to the console,
                                          useful for debugging if you feel like something is not working

    @description: This function is the function that starts framework and starts advertising
    """
    global m_user_callback,\
           m_server_log_output_path,\
           m_server_list,\
           m_debug,\
           m_client

    m_client = CLIENT()
    m_server_log_output_path = server_log_output    ## Path to folder where to crete server logs
    m_debug = debug                                 ## Print trace messages to the console for debugging purposes
    m_server_list = server_list                     ## List of guild objects to iterate thru in the advertiser task
    m_user_callback = user_callback                 ## Called after framework has started

    if is_user:
        trace("Bot is an user account which is against discord's ToS",TraceLEVELS.WARNING)
    m_client.run(token, bot=not is_user)
