"""
    ~   message    ~
    This module contains the definitions regarding the xxxMESSAGE class and
    all the functionality for sending data into discord channels.
"""
from    typing import Dict, List, Union, Literal
from    .dtypes import *
from    .tracing import *
from    .const import *
from    . import client
import  random
import  time
import  asyncio
import  _discord as discord


__all__ = (
    "TextMESSAGE",
    "VoiceMESSAGE",
    "DirectMESSAGE"
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
        if not self.running:
            self.running = True
            self.startms = time.time()

    def elapsed(self):
        """Return the timer elapsed from last reset
           and starts the timer if not already stared"""
        if self.running:
            return time.time() - self.startms
        self.start()
        return 0

    def reset (self):
        "Reset the timer"
        self.running = False


class BaseMESSAGE:
    """
        ~  BaseMESSAGE  ~
        @Info:
        This is the base class for all the different classes that
        represent a message you want to be sent into discord.
    """
    __slots__ = (
        "randomized_time",
        "period",
        "random_range",
        "timer",
        "force_retry",
        "data"
    )
    # The "__valid_data_types__" should be implemented in the INHERITED classes.
    # The set contains all the data types that the class is allowed to accept, this variable
    # is then checked for allowed data types in the "initialize" function bellow.
    __valid_data_types__ = {}

    def __init__(self,
                start_period : Union[float,None],
                end_period : float,
                data,
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
        self.data = data

    def generate_log_context(self):
        """ ~ generate_log_context ~
            @Info:
            This method is used for generating a dictionary (later converted to json) of the
            data that is to be included in the message log. This is to be implemented inside the
            inherited classes.
        """
        raise NotImplementedError

    def is_ready(self) -> bool:
        """
        Name:   is_ready
        Param:  void
        Info:   This
        """
        return not self.force_retry["ENABLED"] and self.timer.elapsed() > self.period or self.force_retry["ENABLED"] and self.timer.elapsed() > self.force_retry["TIME"]

    async def send_channel(self) -> dict:
        """                  ~ send_channel ~
            @Info:
            Sends data to a specific channel, this is seperate from send
            for eaiser implementation of simmilar inherited classes
            @Return:
            The method returns a dictionary containing : {"success": bool, "reason": discord.HTTPException}
            """
        raise NotImplementedError

    async def send(self) -> dict:
        """
        Name:   send to channels
        Param:  void
        Info:   This function should be implemented in the inherited class
                and should send the message to all the channels."""
        raise NotImplementedError

    async def initialize_channels(self) -> bool:
        """
            ~  initialize_channels  ~
            This method initializes the implementation specific
            api objects and checks for the correct channel inpit context.
        """
        raise NotImplementedError

    async def initialize_data(self) -> bool:
        """
            ~  initialize_data  ~
            This method checks for the correct data input to the xxxMESSAGE
            object. The expected datatypes for specific implementation is
            defined thru the static variable __valid_data_types__
        """
        # Check for correct data types of the MESSAGE.data parameter
        if not isinstance(self.data, FunctionBaseCLASS):
            # This is meant only as a pre-check if the parameters are correct so you wouldn't eg. start
            # sending this message 6 hours later and only then realize the parameters were incorrect.
            # The parameters also get checked/parsed each period right before the send.

            # Convert any arguments passed into a list of arguments
            if  isinstance(self.data, (list, tuple, set)):
                self.data = list(self.data)   # Convert into a regular list to allow removal of items
            else:
                self.data = [self.data]       # Place into a list for iteration, to avoid additional code

            # Check all the arguments
            for data in self.data[:]:
                # Check all the data types of all the passed to the data parameter.
                # If class does not match the allowed types, then the object is removed.
                # The for loop iterates thru a shallow copy (sliced list) of data_params to allow removal of items
                # without affecting the iteration (would skip elements without a copy or use of while loop).

                # The inherited classes MUST DEFINE THE "__valid_data_types__" inside the class which should be a set of the allowed data types

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
            ~ initialize ~
            @Info:
            The initialize method initilizes the message object.
            @Params:
            - options ~ custom keyword arguments, this differes from inher. to inher. class that
            is inherited from the BaseGUILD class and must be matched in the inherited class from BaseMESSAGE that
            you want to use in that specific inherited class from BaseGUILD class"""
        if not await self.initialize_channels(**options):
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

    def generate_log_context(self,
                             sent_audio: AUDIO,
                             succeeded_ch: List[discord.VoiceChannel],
                             failed_ch: List[dict]):
        """ ~ generate_log_context ~
            @Param:
                sent_audio: AUDIO -- The audio that was streamed to the channels
                succeeded_ch: List[discord.VoiceChannel] -- list of the successfuly streamed channels,
                failed_ch: List[dict]   -- list of dictionaries contained the failed channel and the Exception
            @Info:
                Generates a dictionary containing data that will be saved in the message log
        """
        succeeded_ch = [{"name": str(channel), "id" : channel.id} for channel in succeeded_ch]
        failed_ch = [{"name": str(entry["channel"]), "id" : entry["channel"].id, "reason": str(entry["reason"])} for entry in failed_ch]
        return {
            "streamed_audio" : sent_audio.filename,
            "channels": {
                "successful" : succeeded_ch,
                "failed": failed_ch
            },
            "type" : type(self).__name__
        }

    async def initialize_channels(self) -> bool:
        ch_i = 0
        cl = client.get_client()
        while ch_i < len(self.channels):
            channel_id = self.channels[ch_i]
            channel = cl.get_channel(channel_id)
            self.channels[ch_i] = channel

            if channel is None:
                trace(f"Unable to get channel from ID {channel_id}", TraceLEVELS.ERROR)
                self.channels.remove(channel)
            elif type(channel) is not discord.VoiceChannel:
                trace(f"VoiceMESSAGE object got ID ({channel_id}) for {type(channel).__name__}, but was expecting {discord.VoiceChannel.__name__}", TraceLEVELS.ERROR)
                self.channels.remove(channel)
            else:
                ch_i += 1

        return len(self.channels) > 0

    async def send_channel(self,
                           channel: discord.VoiceChannel,
                           audio: AUDIO) -> dict:
        stream = None
        voice_client = None
        try:
            # Try to open file first as FFMpegOpusAudio doesn't raise exception if file does not exist
            with open(audio.filename, "rb"):
                pass
            stream = discord.FFmpegOpusAudio(audio.filename)

            voice_client = await channel.connect(timeout=C_VC_CONNECT_TIMEOUT)
            voice_client.play(stream)
            while voice_client.is_playing():
                await asyncio.sleep(1)
            return {"success": True}
        except Exception as ex:
            return {"success": False, "reason": ex}
        finally:
            if stream is not None:
                stream.cleanup()
            if voice_client is not None:
                # Note (TODO): Should remove this in the future. Currently it disconnects instead moving to a different channel, because using
                #         .move_to(channel) method causes some sorts of "thread leak" (new threads keep getting created, waiting for pycord to fix this).
                await voice_client.disconnect()

    async def send(self) -> Union[dict,  None]:
        """"
            ~  send  ~
            @Info:
                Streams audio into the chanels
            @Return:
                Returns a dictionary generated by the generate_log_context method
                or the None object if message wasn't ready to be sent
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
            # These block isn't really neccessary as it really only accepts one type and that is AUDIO,
            # but it is written like this to make it analog to the TextMESSAGE parsing code in the send
            if not isinstance(data_to_send, (list, tuple, set)):
                # Put into a list for easier iteration
                data_to_send = (data_to_send,)

            for element in data_to_send:
                if type(element) is AUDIO:
                    audio_to_stream = element

        if audio_to_stream is not None:
            errored_channels = []
            succeded_channels= []

            for channel in self.channels:
                context = await self.send_channel(channel, audio_to_stream)
                if context["success"]:
                    succeded_channels.append(channel)
                else:
                    errored_channels.append({"channel":channel, "reason": context["reason"]})

            # Remove any channels that returned with code status 404 (They no longer exist)
            for data in errored_channels:
                reason = data["reason"]
                channel = data["channel"]
                if isinstance(reason, discord.HTTPException) and reason.status == 404 and reason.code == 10003:
                    self.channels.remove(channel)
                    trace(f"Channel {channel.name}(ID: {channel.id}) was deleted, removing it from the send list", TraceLEVELS.WARNING)

            return self.generate_log_context(audio_to_stream, succeded_channels, errored_channels)
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

    def generate_log_context(self,
                             sent_text : str,
                             sent_embed : EMBED,
                             sent_files : List[FILE],
                             succeeded_ch: List[Union[discord.TextChannel, discord.Thread]],
                             failed_ch: List[dict]):
        """ ~ generate_log_context ~
            @Param:
                sent_text : str -- The text that was sent
                sent_embed : EMBED  -- The embed that was sent
                sent_files : List[FILE] -- List of files that were sent
                succeeded_ch: List[discord.VoiceChannel] -- list of the successfuly streamed channels,
                failed_ch: List[dict]   -- list of dictionaries contained the failed channel and the Exception
            @Info:
                Generates a dictionary containing data that will be saved in the message log
        """
        succeeded_ch = [{"name": str(channel), "id" : channel.id} for channel in succeeded_ch]
        failed_ch = [{"name": str(entry["channel"]), "id" : entry["channel"].id, "reason": str(entry["reason"])} for entry in failed_ch]

        #Generate embed
        if sent_embed is not None:
            EmptyEmbed = discord.embeds.EmptyEmbed
            sent_embed : dict = {
                "title" : sent_embed.title if sent_embed.title is not EmptyEmbed else None,
                "author" : sent_embed.author.name if sent_embed.author.name is not EmptyEmbed else None,
                "thumbnail" : sent_embed.thumbnail.url if sent_embed.thumbnail.url is not EmptyEmbed else None,
                "image" : sent_embed.image.url if sent_embed.image.url is not EmptyEmbed else None,
                "description" : sent_embed.description if sent_embed.description is not EmptyEmbed else None,
                "color" : sent_embed.colour if sent_embed.colour is not EmptyEmbed else None,
                "fields" : sent_embed._fields if hasattr(sent_embed, "_fields") else None
            }
            for key in sent_embed.copy():
                # Pop items that are None to reduce the log length
                if sent_embed[key] is None:
                    sent_embed.pop(key)

        # Generate files
        sent_files = [x.filename for x in sent_files]

        sent_data_context = {}
        if sent_text is not None:
            sent_data_context["text"] = sent_text
        if sent_embed is not None:
            sent_data_context["embed"] = sent_embed
        if len(sent_files):
            sent_data_context["files"] = sent_files

        return {
            "sent_data": {
                **sent_data_context
            },
            "channels": {
                "successful" : succeeded_ch,
                "failed": failed_ch
            },
            "type" : type(self).__name__,
            "mode" : self.mode,
        }

    async def initialize_channels(self) -> bool:
        ch_i = 0
        cl = client.get_client()
        while ch_i < len(self.channels):
            channel_id = self.channels[ch_i]
            channel = cl.get_channel(channel_id)
            self.channels[ch_i] = channel

            if channel is None:
                trace(f"Unable to get channel from ID {channel_id}", TraceLEVELS.ERROR)
                self.channels.remove(channel)
            elif type(channel) not in {discord.TextChannel, discord.Thread}:
                trace(f"TextMESSAGE object got ID ({channel_id}) for {type(channel).__name__}, but was expecting {discord.TextChannel.__name__}", TraceLEVELS.ERROR)
                self.channels.remove(channel)
            else:
                ch_i += 1

        return len(self.channels) > 0
    
    async def send_channel(self,
                           channel: discord.TextChannel,
                           text: str,
                           embed: EMBED,
                           files: List[FILE]) -> dict:

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
                if  (self.mode in  {"send" , "clear-send"} or
                    self.mode == "edit" and self.sent_messages[channel.id] is None
                    ):
                    discord_sent_msg = await channel.send(  text,
                                                            embed=embed,
                                                            # Create discord.File objects here so it is catched by the except block and then logged
                                                            files=[discord.File(fwFILE.filename) for fwFILE in files])
                    self.sent_messages[channel.id] = discord_sent_msg
                # Mode is edit and message was already send to this channel
                elif self.mode == "edit":
                    await self.sent_messages[channel.id].edit ( text,
                                                                embed=embed)

                return {"success" : True}

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
                        else:
                            exit_condition = True
                    else:
                        exit_condition = True
                else:
                    exit_condition = True

                # Assume a fail
                if exit_condition:
                    return {"success" : False, "reason" : ex}

    async def send(self) -> Union[dict,  None]:
        """"
            ~  send  ~
            @Info:
                Sends the data into the channels
            @Return:
                Returns a dictionary generated by the generate_log_context method
                or the None object if message wasn't ready to be sent
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
                # Put into a list for easier iteration.
                # Technically only necessary if self.data  is a function (dynamic return),
                # since normal (str, EMBED, FILE) get pre-checked in initialization.
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
                context = await self.send_channel(channel, text_to_send,
                                                  embed_to_send,
                                                  files_to_send)
                if context["success"]:
                    succeded_channels.append(channel)
                else:
                    errored_channels.append({"channel":channel, "reason": context["reason"]})

            # Remove any channels that returned with code status 404 (They no longer exist)
            for data in errored_channels:
                reason = data["reason"]
                channel = data["channel"]
                if isinstance(reason, discord.HTTPException) and reason.status == 404 and reason.code == 10003:
                    self.channels.remove(channel)
                    trace(f"Channel {channel.name}(ID: {channel.id}) was deleted, removing it from the send list", TraceLEVELS.WARNING)

            # Return sent data + failed and successful function for logging purposes
            return self.generate_log_context(text_to_send, embed_to_send, files_to_send, succeded_channels, errored_channels)

        return None


class DirectMESSAGE(BaseMESSAGE):
    """~ BaseMESSAGE ~
        @Info:
        DirectMESSAGE represents a message that will be sent into direct messages
        @Params:
        - start_period, end_period:
            dictate the sending period in seconds, if both are > 0, then the period is randomized
            each send and that period will be between the specifiec parameters. If start_period is None,
            the period will be equal to end_period.
        - data:
            Represents data that will be sent into the channels, the data types can be:
            - str, EMBED, FILE, list of str, EMBED, FILE or a function (refer to README)
        - mode:
            Mode parameter dictates the behaviour of the way data is send. It can be:
            - "send" ~ Each period a new message will be send to Discord,
            - "edit" ~ Each period the previous message will be edited, or a new sent if the previous message does not exist/was deleted
            - "clear-send" ~ Each period the previous message will be cleared and a new one sent to the channels.
        - start_now:
            Dictates if the message should be sent immediatly after framework start or if it should wait it's period first and then send
        """

    __slots__ = (
        "randomized_time",
        "period",
        "random_range",
        "timer",
        "force_retry",
        "data",
        "mode",
        "previous_message",
        "dm_channel"
    )
    __valid_data_types__ = {str, EMBED, FILE}
    def __init__(self,
                 start_period: Union[float, None],
                 end_period: float,
                 data: Union[str, EMBED, FILE, list],
                 mode: Literal["send", "edit", "clear-send"] = "send",
                 start_now: bool = True):
        super().__init__(start_period, end_period, start_now)
        self.data = data
        self.mode = mode
        self.dm_channel = None
        self.previous_message = None

    def generate_log_context(self,
                             sent_text : str,
                             sent_embed : EMBED,
                             sent_files : List[FILE],
                             **success_context):
        """ ~ generate_log_context ~
            @Param:
                sent_text : str -- The text that was sent
                sent_embed : EMBED  -- The embed that was sent
                sent_files : List[FILE] -- List of files that were sent
                succeeded_ch: List[discord.VoiceChannel] -- list of the successfuly streamed channels,
                failed_ch: List[dict]   -- list of dictionaries contained the failed channel and the Exception
            @Info:
                Generates a dictionary containing data that will be saved in the message log
        """
        #Generate embed
        if sent_embed is not None:
            EmptyEmbed = discord.embeds.EmptyEmbed
            sent_embed : dict = {
                "title" : sent_embed.title if sent_embed.title is not EmptyEmbed else None,
                "author" : sent_embed.author.name if sent_embed.author.name is not EmptyEmbed else None,
                "thumbnail" : sent_embed.thumbnail.url if sent_embed.thumbnail.url is not EmptyEmbed else None,
                "image" : sent_embed.image.url if sent_embed.image.url is not EmptyEmbed else None,
                "description" : sent_embed.description if sent_embed.description is not EmptyEmbed else None,
                "color" : sent_embed.colour if sent_embed.colour is not EmptyEmbed else None,
                "fields" : sent_embed._fields if hasattr(sent_embed, "_fields") else None
            }
            for key in sent_embed.copy():
                # Pop items that are None to reduce the log length
                if sent_embed[key] is None:
                    sent_embed.pop(key)

        # Generate files
        sent_files = [x.filename for x in sent_files]

        if not success_context["success"]:
            success_context["reason"] = str(success_context["reason"])

        sent_data_context = {}
        if sent_text is not None:
            sent_data_context["text"] = sent_text
        if sent_embed is not None:
            sent_data_context["embed"] = sent_embed
        if len(sent_files):
            sent_data_context["files"] = sent_files

        return {
            "sent_data": {
                **sent_data_context
            },
            "success_info": {
                **success_context
            },
            "type" : type(self).__name__,
            "mode" : self.mode
        }

    async def initialize_channels(self,
                                  user_id) -> bool:
        """~ initialize_channels ~
        @Info:
        The method creates a direct message channel and
        returns True on success or False on failure
        @Parameters:
        - options ~ dictionary containing key with user_id
                    (sent to by the USER instance's initialize method)
        """
        cl = client.get_client()
        self.dm_channel = cl.get_user(user_id)
        if self.dm_channel is None:
            return False
        return True

    async def send_channel(self,
                           text: str,
                           embed: EMBED,
                           files: List[FILE]) -> dict:
        """
            ~ send_channel ~
            @Info:
            Sends data to the DM channel (user).
            @Return:
            - dict:
                - "success" : bool ~ True if successful, else False
                - "reason"  : Exception ~ Only present if "success" is False,
                              contains the Exception returned by the send attempt.
        """
        if self.mode == "clear-send" and self.previous_message is not None:
            for tries in range(3):
                try:
                    # Delete discord message that originated from this MESSAGE object
                    await self.previous_message.delete()
                    self.previous_message = None
                    break
                except discord.HTTPException as ex:
                    if ex.status == 429:
                        await asyncio.sleep(int(ex.response.headers["Retry-After"])  + 1)

        # Send/Edit messages
        for tries in range(3):  # Maximum 3 tries (if rate limit)
            try:
                # Mode dictates to send new message or delete previous and then send new message or mode dictates edit but message was  never sent to this channel before
                # Rate limit avoidance
                if  self.mode in  {"send" , "clear-send"} or\
                    self.mode == "edit" and self.previous_message is None:
                    discord_sent_msg = await self.dm_channel.send(  text,
                                                            embed=embed,
                                                            # Create discord.File objects here so it is catched by the except block and then logged
                                                            files=[discord.File(fwFILE.filename) for fwFILE in files])
                    self.previous_message = discord_sent_msg

                # Mode is edit and message was already send to this channel
                elif self.mode == "edit":
                    await self.previous_message.edit(text,
                                                     embed=embed)
                return {"success" : True}

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
                            self.previous_message  = None
                        else:
                            exit_condition = True
                    else:
                        exit_condition = True
                else:
                    exit_condition = True

                # Assume a fail
                if exit_condition:
                    return {"success" : False, "reason" : ex}

    async def send(self) -> Union[dict, None]:
        """"
            ~  send  ~
            @Info:
                Sends the data into the DM channel of the user.
            @Return:
                Returns a dictionary generated by the generate_log_context method
                or the None object if message wasn't ready to be sent
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

        if text_to_send is not None or embed_to_send is not None or len(files_to_send) > 0:
                # Clear previous messages sent to channel if mode is MODE_DELETE_SEND
            context = await self.send_channel(text_to_send, embed_to_send, files_to_send)

            # Return sent data + failed and successful function for logging purposes
            return self.generate_log_context(text_to_send, embed_to_send, files_to_send, **context)

        return None
