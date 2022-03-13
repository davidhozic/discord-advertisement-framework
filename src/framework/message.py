from    typing import List, Union, Tuple, Literal
from    .dtypes import *
from    .tracing import *
from    .const import *
from    . import client
import  random
import  _discord as discord
import  time
import  asyncio

__all__ = (
    "TextMESSAGE",
    "VoiceMESSAGE"
)

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


class BaseMESSAGE:
    __slots__ = (
        "randomized_time",
        "period",
        "random_range",
        "timer",
        "force_retry"
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
                start_now : bool=True):

        if start_period is None:            # If start_period is none -> period will not be randomized
            self.randomized_time = False
            self.period = end_period
        else:
            self.randomized_time = True
            self.random_range = (start_period, end_period)
            self.period = random.randrange(*self.random_range)  # This will happen after each sending as well

        self.timer = TIMER()
        self.force_retry = {"ENABLED" : start_now, "TIME" : 0}  # This is used in both TextMESSAGE and VoiceMESSAGE for compatability purposes
        

    def is_ready(self) -> bool:
        """
        Name:   is_ready
        Param:  void
        Info:   This
        """
        return not self.force_retry["ENABLED"] and self.timer.elapsed() > self.period or self.force_retry["ENABLED"] and self.timer.elapsed() > self.force_retry["TIME"]

    def send(self):
        """
        Name:   send to channels
        Param:  void
        Info:   This function should be implemented in the inherited class
                and should send the message to all the channels."""
        raise NotImplementedError
    
    async def initialize_channels(self,
                                  options) -> bool:
        raise NotImplementedError
    
    async def initialize_data(self) -> bool:
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
                        trace(f"INVALID DATA PARAMETER PASSED!\nArgument is of type : {type(data).__name__}\nSee README.md for allowed data types", TraceLEVELS.WARNING)
                        self.data.remove(data)
            
            return len(self.data) > 0

        return True

    async def initialize(self, **options) -> bool:
        """
        Name:   initialize
        Param:
            - guild_name: str  ::   Name of the guild that owns the channels.
                                    This is only used for trace messages for easier debugging.
            - guild_id: int    ::   Snowflake id of the guild that owns the message channels.
                                    This parameter is used to check if the channels really belong to this guild and not some other,
                                    and is also used for trace messages for easier debugging of incorrectly passed parameters."""

        if not await self.initialize_channels(options):
            return False

        if not await self.initialize_data():
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

        super().__init__(start_period, end_period, start_now)
        self.data = data
        self.channels = channel_ids
    
    async def initialize_channels(self, options) -> bool:
        ch_i = 0
        cl = client.get_client()
        while ch_i < len(self.channels):
            channel_id = self.channels[ch_i]
            channel = cl.get_channel(channel_id)

            if type(channel) is not discord.VoiceChannel:
                trace(f"TextMESSAGE object got id for {type(channel).__name__}, but was expecting {discord.VoiceChannel.__name__}", TraceLEVELS.ERROR)
                channel = None

            self.channels[ch_i] = channel

            if channel is None:
                self.channels.remove(channel)
            else:
                ch_i += 1

        return len(self.channels) > 0

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

    async def send(self) -> Union[Tuple[str, list, list],  None]:
        """
        Name: send
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
                but it is written like this to make it analog to the TextMESSAGE parsing code in the send"""
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

            return {"data_context": self.stringify_sent_data(audio_to_stream), "succeeded_ch": succeded_channels, "failed_ch" : errored_channels}
        
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
        super().__init__(start_period, end_period, start_now)
        self.data = data
        self.mode = mode
        self.channels = channel_ids
        self.sent_messages = {ch_id : None for ch_id in channel_ids}

    async def initialize_channels(self, options) -> bool:
        ch_i = 0
        cl = client.get_client()
        while ch_i < len(self.channels):
            channel_id = self.channels[ch_i]
            channel = cl.get_channel(channel_id)

            if type(channel) is not discord.TextChannel:
                trace(f"TextMESSAGE object got id for {type(channel).__name__}, but was expecting {discord.TextChannel.__name__}", TraceLEVELS.ERROR)
                channel = None

            self.channels[ch_i] = channel

            if channel is None:
                self.channels.remove(channel)
            else:
                ch_i += 1

        return len(self.channels) > 0

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
{sent_files}'''

    async def send(self) -> Union[Tuple[str, list, list],  None]:
        """
        Name: send
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
                        else:
                            exit_condition = True

                        # Assume a fail
                        if exit_condition:
                            errored_channels.append({"channel":channel, "reason":ex})
                            break

            # Return sent data + failed and successful function for logging purposes
            return {"data_context": self.stringify_sent_data(text_to_send, embed_to_send, files_to_send), "succeeded_ch": succeded_channels, "failed_ch" : errored_channels}

        return None
