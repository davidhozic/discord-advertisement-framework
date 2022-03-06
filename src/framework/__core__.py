"""
    DISCORD ADVERTISEMENT FRAMEWORK (DAF)
    Author      :: David Hozic
    Copyright   :: Copyright (c) 2022 David Hozic
    Version     :: V1.7.8
"""
from    contextlib import suppress
from    typing import Literal, Union, List, Tuple, Any, Optional
from    enum import Enum, auto
import  time
import  asyncio
import  random
import  os
import  _discord as discord
import  datetime
import  copy

if __name__ == "__main__":
    raise ImportError("This file is meant as a module and not as a script to run directly. Import it in a sepereate file and run it there")

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
    "AUDIO",
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

C_RT_AVOID_DELAY     = 1    # Rate limit avoidance delay
C_TASK_SLEEP_DELAY   = 0.1  # Advertiser task sleep
C_VC_CONNECT_TIMEOUT = 1    # Timeout of voice channels

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
        timestruct = time.localtime()
        timestamp = "Date: {:02d}.{:02d}.{:04d} Time:{:02d}:{:02d}"
        timestamp = timestamp.format(timestruct.tm_mday,
                                         timestruct.tm_mon,
                                         timestruct.tm_year,
                                         timestruct.tm_hour,
                                         timestruct.tm_min)
        l_trace = f"{timestamp}\nTrace level: {level.name}\nMessage: {message}\n"
        print(l_trace)

#######################################################################
# Decorators
#######################################################################
class FunctionBaseCLASS:
    """
    type: dummy class
    name: FunctionBaseCLASS
    info: Used as a base class to FunctionCLASS which gets created in framework.data_function decorator.
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
        Name:  FunctionCLASS
        Info:  Used for creating special classes that are then used to create objects in the framework.MESSAGE
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
        """Return the timer elapsed from last reset
           and starts the timer if not already stared"""
        if self.running:
            return time.time() - self.startms
        else:
            self.start()
            return 0

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
    def __init__(self, *, loop: Optional[asyncio.AbstractEventLoop] = None, **options: Any):
        super().__init__(loop=loop, **options)

    async def on_ready(self) -> None:
        """
        Name : on_ready
        Info : Tasks that is started by pycord when you have been successfully logged into discord.
        """
        trace(f"Logged in as {self.user}", TraceLEVELS.NORMAL)

        if initialize():
            # Initialization was successful, so create the advertiser task and start advertising.
            trace("Successful initialization!",TraceLEVELS.NORMAL)
            asyncio.gather(
                    asyncio.create_task(advertiser("t_messages")),  # Task for sending text messages
                    asyncio.create_task(advertiser("vc_messages"))  # Task for sending voice messages
                )
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
            for field in fields:
                self.add_field(name=field.name,value=field.content,inline=field.inline)


class FILE:
    """
    Name:   FILE
    Param:
        -   filename:
            string path to the file you want to send

    Info:   FILE object used as a data parameter to the MESSAGE objects.
            This is needed aposed to a normal file object because this way,
            you can edit the file after the framework has already been started.
    """
    __slots__ = ("filename",)
    def __init__(self,
                 filename):
        self.filename = filename


class AUDIO(FILE):
    """
    Name: AUDIO
    Param:
        -   filename:
            string path to the audio you want to stream
    Info: Represents an audio parameter that is used in the VoiceMESSAGE data parameterer
    """
    __slots__ = ("filename",)


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

    """
    The "__valid_data_types__" should be implemented in the INHERITED classes.
    The set contains all the data types that the class is allowed to accept, this variable
    is then checked for allowed data types in the "initialize" function bellow.
    """
    __valid_data_types__ = {}

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
        self.force_retry = {"ENABLED" : start_now, "TIME" : 0}  # This is used in both TextMESSAGE and VoiceMESSAGE for compatability purposes
        self.sent_messages = {ch_id : None for ch_id in channel_ids}

    def is_ready(self) -> bool:
        """
        Name:   is_ready
        Param:  void
        Info:   This
        """
        return not self.force_retry["ENABLED"] and self.timer.elapsed() > self.period or self.force_retry["ENABLED"] and self.timer.elapsed() > self.force_retry["TIME"]

    def send_to_channels(self) -> Union[Tuple[str, list, list],  None]:
        """
        Name:   send to channels
        Param:  void
        Info:   This function should be implemented in the inherited class
                and should send the message to all the channels.
        Return: The function should return:
            - stringified (partial) log of sent data, list of successful channels and failed channels
            - None if message was not ready to be sent (use of a function to ge the data)
        """
        raise NotImplementedError

    def initialize( self,
                    guild_name: str,
                    guild_id: int) -> bool:
        """
        Name:   initialize
        Param:
            - guild_name: str  ::   Name of the guild that owns the channels.
                                    This is only used for trace messages for easier debugging.
            - guild_id: int    ::   Snowflake id of the guild that owns the message channels.
                                    This parameter is used to check if the channels really belong to this guild and not some other,
                                    and is also used for trace messages for easier debugging of incorrectly passed parameters."""

        # Remove duplicated channel ids
        for channel_id in self.channels[:]:
            if self.channels.count(channel_id) > 1:
                trace(f"Guild \"{guild_name}\" (ID: {guild_id}) has duplicated channel (ID: {channel_id})", TraceLEVELS.WARNING)
                self.channels.remove(channel_id)
        # Transform channel ids into pycord channel objects
        channel_i = 0
        while channel_i < len(self.channels):
            """
            Replace the channel IDs with channel objects.
            while loop is used as I don't want the index to increase every iteration
            """
            channel_id = self.channels[channel_i]
            self.channels[channel_i] = m_client.get_channel(channel_id)
            channel = self.channels[channel_i]

            if channel is None:
                # Unable to find the channel objects, ergo remove.
                trace(f"Unable to get channel from id: {channel_id} (Does not exist - Incorrect ID?) in GUILD: \"{guild_name}\" (ID: {guild_id})", TraceLEVELS.WARNING)
                self.channels.remove(channel)

            elif channel.guild.id != guild_id:
                # The channel is not part of this guild, ergo remove.
                trace(f"Guild \"{guild_name}\" (ID: {guild_id}) has no channel \"{channel.name}\" (ID: {channel_id})", TraceLEVELS.WARNING)
                self.channels.remove(channel)
            else:
                channel_i += 1

        # Check for correct data types of the MESSAGE.data parameter
        if not isinstance(self.data, FunctionBaseCLASS):
            """
            This is meant only as a pre-check if the parameters are correct so you wouldn't eg. start
            sending this message 6 hours later and only then realize the parameters were incorrect.
            The parameters also get checked/parsed each period right before the send.
            """
            # Convert any arguments passed into a list of arguments
            if  isinstance(self.data, (list, tuple, set)):
                self.data = list(self.data)   # Convert into a regular list to allow removal of items
            else:
                self.data = [self.data]       # Place into a list for iteration, to avoid additional code

            # Check all the arguments
            for data in self.data[:]:
                """
                Check all the data types of all the passed to the data parameter.
                If class does not match the allowed types, then the object is removed.
                The for loop iterates thru a shallow copy (sliced list) of data_params to allow removal of items
                without affecting the iteration (would skip elements without a copy or use of while loop).

                The inherited classes MUST DEFINE THE "__valid_data_types__" inside the class which should be a set of the allowed data types
                """
                if (
                        type(data) not in type(self).__valid_data_types__
                    ):
                    if isinstance(self.data, FunctionBaseCLASS):
                        trace(f"The function can only be used on the data parameter directly, not in a list\nFunction: {data.func_name}", TraceLEVELS.ERROR)
                        self.data.clear()
                        break
                    else:
                        trace(f"INVALID DATA PARAMETER PASSED!\nArgument is of type : {type(data).__name__}\nSee README.md for allowed data types\nGUILD: {guild_name} (ID: {guild_id})", TraceLEVELS.WARNING)
                        self.data.remove(data)

        # Check if any data params are left and remove the message object if not
        if (not len(self.channels) or
            not isinstance(self.data, FunctionBaseCLASS) and not len(self.data)):   # if isinstance FunctionBaseCLASS, then it has no len, and because of short-circuit, len will not be read
            # Unable to parse the message, return False to let the guild know it must be removed
            return False

        return True


class VoiceMESSAGE(BaseMESSAGE):
    """
    Name: VoiceMESSAGE
    Info: The VoiceMESSAGE object containts parameters which describe behaviour and data that will be sent to the channels.
    Params:
    - Start Period , End Period (start_period, end_period) - These 2 parameters specify the period on which the messages will be played:
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
        "force_retry",
    )

    __valid_data_types__ = {AUDIO}  # This is used in the BaseMESSAGE.initialize() to check if the passed data parameters are of correct type

    def __init__(self, start_period: Union[float, None],
                 end_period: float,
                 data: AUDIO,
                 channel_ids: List[int],
                 start_now: bool = True):

        super().__init__(start_period, end_period, channel_ids, start_now)
        self.data = data

    def stringify_sent_data (self,
                            sent_audio: AUDIO):
        """
        Name:  stringify_sent_data
        Param: sent_audio -- Audio file that was streamed to the channels
        Info:  Returns a string representation of send data to the channels.
               This is then used as a data_context parameter to the GUILD object.
        """
        return f'''
## Streamed AUDIO:
{sent_audio.filename}
'''

    async def send_to_channels(self) -> Union[Tuple[str, list, list],  None]:
        """
        Name: send_to_channels
        Params: void
        info: sends messages to all the channels
        """
        self.timer.reset()
        self.timer.start()
        self.force_retry["ENABLED"] = False
        if self.randomized_time is True:
            self.period = random.randrange(*self.random_range)

        data_to_send  = None
        if isinstance(self.data, FunctionBaseCLASS):
            data_to_send = self.data.get_data()
        else:
            data_to_send = self.data

        audio_to_stream = None
        if data_to_send is not None:
            """ These block isn't really neccessary as it really only accepts one type and that is AUDIO,
                but it is written like this to make it analog to the TextMESSAGE parsing code in the send_to_channels"""
            if not isinstance(data_to_send, (list, tuple, set)):
                # Put into a list for easier iteration
                data_to_send = (data_to_send,)

            for element in data_to_send:
                if type(element) is AUDIO:
                    audio_to_stream = element

        if audio_to_stream is not None:
            errored_channels = []
            succeded_channels= []
            voice_client = None

            for channel in self.channels:
                try:
                    stream = None
                    # Try to open file first as FFMpegOpusAudio doesn't raise exception if file does not exist
                    with open(audio_to_stream.filename, "rb") as reader: pass
                    stream = discord.FFmpegOpusAudio(audio_to_stream.filename)
                        
                    voice_client = await channel.connect(timeout=C_VC_CONNECT_TIMEOUT)
                    voice_client.play(stream)
                    while voice_client.is_playing():
                        await asyncio.sleep(1)
                    succeded_channels.append(channel)
                except Exception as ex:
                    errored_channels.append({"channel":channel, "reason":f"{type(ex).__name__} : {ex}"})
                finally:
                    if stream is not None:
                        stream.cleanup()
                    if voice_client is not None:
                        """
                        Note (TODO): Should remove this in the future. Currently it disconnects instead moving to a different channel, because using
                              .move_to(channel) method causes some sorts of "thread leak" (new threads keep getting created, waiting for pycord to fix this).
                        """
                        await voice_client.disconnect()

            return self.stringify_sent_data(audio_to_stream), succeded_channels, errored_channels
        
        return None

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

    __valid_data_types__ = {str, EMBED, FILE}


    def __init__(self, start_period: Union[float, None],
                 end_period: float,
                 data: Union[str, EMBED, FILE,List[Union[str, EMBED, FILE]]],
                 channel_ids: List[int],
                 mode: Literal["send", "edit", "clear-send"] = "send",
                 start_now: bool = True):
        super().__init__(start_period, end_period, channel_ids, start_now)
        self.data = data
        self.mode = mode


    def stringify_sent_data (self,
                            sent_text : str,
                            sent_embed : discord.Embed,
                            sent_files : list):
        """
        Name:  stringify_sent_data
        Param: sent_audio -- Audio file that was streamed to the channels
        Info:  Returns a string representation of send data to the channels.
               This is then used as a data_context parameter to the GUILD object.
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

        # Generate files
        sent_files = "".join(    f"- ```\n  {file.filename}\n  ```\n" for file in sent_files    ).rstrip("\n")

        return f'''
## Text:
{sent_text}
***
## Embed:
{sent_embed}
***
## Files:
{sent_files}
'''
    async def send_to_channels(self) -> Union[Tuple[str, list, list],  None]:
        """
        Name: send_to_channels
        Params: void
        info: sends messages to all the channels
        """
        self.timer.reset()
        self.timer.start()
        self.force_retry["ENABLED"] = False
        if self.randomized_time is True:
            self.period = random.randrange(*self.random_range)

        # Parse data from the data parameter
        data_to_send  = None
        if isinstance(self.data, FunctionBaseCLASS):
            data_to_send = self.data.get_data()
        else:
            data_to_send = self.data

        embed_to_send = None
        text_to_send  = None
        files_to_send  = []
        if data_to_send is not None:
            if not isinstance(data_to_send, (list, tuple, set)):
                """ Put into a list for easier iteration.
                    Technically only necessary if self.data  is a function (dynamic return),
                    since normal (str, EMBED, FILE) get pre-checked in initialization."""
                data_to_send = (data_to_send,)

            for element in data_to_send:
                if isinstance(element, str):
                    text_to_send = element
                elif isinstance(element, EMBED):
                    embed_to_send = element
                elif isinstance(element, FILE):
                    files_to_send.append(element)

        # Send messages
        if text_to_send is not None or embed_to_send is not None or len(files_to_send) > 0:
            errored_channels = []
            succeded_channels= []

            # Send to channels
            for channel in self.channels:
                # Clear previous messages sent to channel if mode is MODE_DELETE_SEND
                if self.mode == "clear-send" and self.sent_messages[channel.id] is not None:
                    for tries in range(3):
                        try:
                            # Delete discord message that originated from this MESSAGE object
                            await self.sent_messages[channel.id].delete()
                            self.sent_messages[channel.id] = None
                            break
                        except discord.HTTPException as ex:
                            if ex.status == 429:
                                await asyncio.sleep(int(ex.response.headers["Retry-After"])  + 1)

                # Send/Edit messages
                for tries in range(3):  # Maximum 3 tries (if rate limit)
                    try:
                        # Mode dictates to send new message or delete previous and then send new message or mode dictates edit but message was  never sent to this channel before
                        # Rate limit avoidance
                        await asyncio.sleep(C_RT_AVOID_DELAY)
                        if  self.mode in  {"send" , "clear-send"} or\
                            self.mode == "edit" and self.sent_messages[channel.id] is None:
                            discord_sent_msg = await channel.send(  text_to_send,
                                                                    embed=embed_to_send,
                                                                    # Create discord.File objects here so it is catched by the except block and then logged
                                                                    files=[discord.File(fwFILE.filename) for fwFILE in files_to_send])
                            self.sent_messages[channel.id] = discord_sent_msg

                        # Mode is edit and message was already send to this channel
                        elif self.mode == "edit":
                            await self.sent_messages[channel.id].edit ( text_to_send,
                                                                        embed=embed_to_send)

                        succeded_channels.append(channel)
                        break    # Break out of the tries loop

                    except Exception as ex:
                        # Failed to send message
                        exit_condition = False
                        if isinstance(ex, discord.HTTPException):
                            if ex.status == 429:    # Rate limit
                                retry_after = int(ex.response.headers["Retry-After"])  + 1
                                if ex.code == 20016:    # Slow Mode
                                    self.force_retry["ENABLED"] = True
                                    self.force_retry["TIME"] = retry_after
                                    exit_condition = True
                                else:   # Normal (write) rate limit
                                    # Rate limit but not slow mode -> put the framework to sleep as it won't be able to send any messages globaly
                                    await asyncio.sleep(retry_after)

                            elif ex.status == 404:      # Unknown object
                                if ex.code == 10008:    # Unknown message
                                    self.sent_messages[channel.id]  = None

                                exit_condition = True
                        else:
                            exit_condition = True

                        # Assume a fail
                        if exit_condition:
                            errored_channels.append({"channel":channel, "reason":ex})
                            break

            # Return sent data + failed and successful function for logging purposes
            return self.stringify_sent_data(text_to_send, embed_to_send, files_to_send), succeded_channels, errored_channels

        return None

class GUILD:
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
        "guild",
        "t_messages",
        "vc_messages",
        "_generate_log",
        "guild_file_name"
    )

    def __init__(self,
                 guild_id : int,
                 messages_to_send : List[Union[TextMESSAGE, VoiceMESSAGE]],
                 generate_log : bool = False):
        self.guild = guild_id
        self.t_messages = []
        self.vc_messages = []

        for message in messages_to_send:
            if type(message) is TextMESSAGE:
                self.t_messages.append(message)
            elif type(message) is VoiceMESSAGE:
                self.vc_messages.append(message)

        self._generate_log = generate_log
        self.guild_file_name = None

    async def advertise(self,
                        attr_message_list: Literal["t_messages", "vc_messages"]):
        """
        Name:   advertise
        Param:  attr_message_list:
                This argument is the name of the messages list attribute.
                This method is called thru 2 different tasks (one for VC and one for Text channels) and it tells us what list to use
        """
        for message in getattr(self, attr_message_list):
            if message.is_ready():
                message_ret = await message.send_to_channels()
                """message.send_to_channels() returns either partial log of sent message,
                succeeded and failed channels or it returns the None object if no data
                was ready to be sent (user function was used to get the data and it returned None)"""
                if self._generate_log and message_ret is not None:
                    self.generate_log(*message_ret)

    def generate_log(self,
                     data_context: str,
                     succeeded_ch: list,
                     failed_ch: List[dict]) -> str:
        """
        Name:   generate_log
        Param:
            - data_context  - str representation of sent data, which is return data of xxxMESSAGE.send_to_channels()
            - succeeded_ch  - list of discord.xxxChannel objects that represent channels that message was successfuly sent into
            - failed_ch     - list of dictionaries where these dictionaries have keys "channel" which's value is discord.xxxChannel object
                              and "reason" which's value is the Exception of why sending failed.
        Info:   Generates a log of a xxxxMESSAGE send attempt
        """
        # Generate timestamp
        timestruct = time.localtime()
        timestamp = "{:02d}.{:02d}.{:04d} {:02d}:{:02d}".format(timestruct.tm_mday,
                                                                timestruct.tm_mon,
                                                                timestruct.tm_year,
                                                                timestruct.tm_hour,
                                                                timestruct.tm_min)
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

        appender_data = f"""
# MESSAGE LOG:
{data_context}
***
## Other data:
-   ```
    Server: {self.guild.name}
    Succeeded in channels: {succeeded_ch}
    Failed in channels: {failed_ch}
    Timestamp: {timestamp}
    ```
***
<br><br><br>
"""
        # Write into file
        try:
            with suppress(FileExistsError):
                os.mkdir(m_server_log_output_path)
            with open(os.path.join(m_server_log_output_path, self.guild_file_name),'a', encoding='utf-8') as appender:
                appender.write(appender_data)
        except OSError as os_exception:
            trace(f"Unable to save log. Exception: {os_exception}", TraceLEVELS.WARNING)

    def initialize(self) -> bool:
        """
        Name:   initialize
        Param:  void
        Return: bool:
                - Returns True if the initialization was successful
                - Returns False if failed, indicating the object should be removed from the server_list
        Info:   The function initializes all the GUILD objects (and other objects inside the GUILD object reccurssively).
                It tries to get the discord.Guild object from the self.guild id and then tries to initialize the MESSAGE objects.
        """
        guild_id = self.guild
        self.guild = m_client.get_guild(guild_id)

        if self.guild is not None:
        # Create a file name without the non allowed characters. Windows' list was choosen to generate the forbidden character because only forbids '/'
            l_forbidden_file_names = ('<','>','"','/','\\','|','?','*',":")
            self.guild_file_name = "".join(char if char not in l_forbidden_file_names else "#" for char in self.guild.name) + ".md"

            for message in self.t_messages[:]:
                """ Iterate thru the slice text messages list and initialize each
                    message object. If the message objects fails to initialize,
                    then it is removed from the original list."""
                if not message.initialize(self.guild.name, guild_id):
                    self.t_messages.remove(message)

            for message in self.vc_messages[:]:
                # Same as above but for voice messages
                if not message.initialize(self.guild.name, guild_id):
                    self.vc_messages.remove(message)

            if not len(self.t_messages) + len(self.vc_messages):
                trace(f"Unable to create server object from server id: {guild_id}", TraceLEVELS.WARNING)
                return False

            return True

        return False

        
#######################################################################
# Tasks
#######################################################################
async def advertiser(message_type: Literal["t_messages", "vc_messages"]) -> None:
    """
    Name  : advertiser
    Param :
        -   message_type:
            Name of the message list variable, can be t_messages for TextMESSAGE list and vc_messages for VoiceMESSAGE list
    Info  : Main task that is responsible for the framework
            2 tasks are created for 2 types of messages: TextMESSAGE and VoiceMESSAGE
    """
    while True:
        await asyncio.sleep(C_TASK_SLEEP_DELAY)
        for guild in m_server_list:
            await guild.advertise(message_type)


#######################################################################
# Functions
#######################################################################
def initialize() -> bool:
    """
    Name:       initialize
    Parameters: void
    Return:     bool:
                - Returns True if ANY guild was successfully initialized
                - Returns False if ALL the guilds were not able to initialize, indicating the framework should be stopped.
    Info:       Function that initializes the guild objects and then returns True on success or False on failure.
    """
    for server in m_server_list[:]:
        if not server.initialize():
            m_server_list.remove(server)

    if len(m_server_list):
        return True
    else:
        trace("No guilds could be parsed", TraceLEVELS.ERROR)
        return False


async def shutdown() -> None:
    """
    Name:   shutdown
    Params: void
    Return: None
    Info:   Stops the framework
    """
    await m_client.close()


def get_client() -> CLIENT:
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
