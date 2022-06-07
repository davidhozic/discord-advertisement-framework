"""
    ~   message    ~
    This module contains the definitions regarding the xxxMESSAGE class and
    all the functionality for sending data into discord channels.
"""
from    typing import List, Union, Literal, Iterable, Any
from    .dtypes import *
from    .tracing import *
from    .const import *
from    .timing import *
from    . import client
from    . import sql
import  random
import  asyncio
import  _discord as discord


__all__ = (
    "TextMESSAGE",
    "VoiceMESSAGE",
    "DirectMESSAGE"
)


class GLOBALS:
    """ ~  GLOBALS  ~
        @Info: Contains the globally needed variables"""
    is_user = True


# Dummy classes for message mods, to use with sql.register_type decorator
@sql.register_type("MessageMODE")
class _:
    __logname__ = "send"
@sql.register_type("MessageMODE")
class _:
    __logname__ = "edit"
@sql.register_type("MessageMODE")
class _:
    __logname__ = "clear-send"


class BaseMESSAGE:
    """~  BaseMESSAGE  ~
        @Info:
        This is the base class for all the different classes that
        represent a message you want to be sent into discord."""

    __slots__ = (
        "initialized",
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
        # If start_period is none -> period will not be randomized
        if start_period is None:            
            self.randomized_time = False
            self.period = end_period
        else:
            self.randomized_time = True
            self.random_range = (start_period, end_period)
            self.period = random.randrange(*self.random_range)

        self.timer = TIMER()
        self.force_retry = {"ENABLED" : start_now, "TIME" : 0}
        self.data = data
        self.initialized = False

    def generate_exception(self, 
                           status: int,
                           code: int,
                           description: str,
                           cls: discord.HTTPException):
        """ ~ method ~
        @Name: generate_exception
        @Info: Generates a discord.HTTPException inherited class exception object
        @Param:
            status: int ~ Atatus code of the exception
            code: int ~ Actual error code
            description: str ~ The textual description of the error
            cls: discord.HTTPException ~ Inherited class to make exception from"""
        resp = Exception()
        resp.status = status
        resp.status_code = status
        resp.reason = cls.__name__
        ex = cls(resp, {"message" : description, "code" : code})
        return ex

    def generate_log_context(self):
        """ ~ method ~
        @Name: generate_log_context
        @Info:
            This method is used for generating a dictionary (later converted to json) of the
            data that is to be included in the message log. This is to be implemented inside the
            inherited classes."""
        raise NotImplementedError
    
    def get_data(self) -> dict:
        """ ~ method ~
        @Name:  get_data
        @Info: Returns a dictionary of keyword arguments that is then expanded
               into other functions (send_channel, generate_log)
               This is to be implemented in inherited classes due to different data_types"""
        raise NotImplementedError

    def is_ready(self) -> bool:
        """ ~ method ~
        @Name:   is_ready
        @Param:  void
        @Info:   This method returns bool indicating if message is ready to be sent"""
        return (not self.force_retry["ENABLED"] and self.timer.elapsed() > self.period or
                self.force_retry["ENABLED"] and self.timer.elapsed() > self.force_retry["TIME"])

    def reset_timer(self) -> None:
        """ ~ method ~
        @Name: restart_time
        @Info: Resets internal timer (and force period)"""
        self.timer.reset()
        self.timer.start()
        self.force_retry["ENABLED"] = False
        if self.randomized_time is True:
            self.period = random.randrange(*self.random_range)

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
        """ ~ async method ~
        Name:   send to channels
        Param:  void
        Info:   This function should be implemented in the inherited class
                and should send the message to all the channels."""
        raise NotImplementedError

    async def initialize_channels(self) -> bool:
        """ ~ async method ~
        @Name: initialize_channels
        @Info: This method initializes the implementation specific
               api objects and checks for the correct channel inpit context."""
        raise NotImplementedError

    async def initialize_data(self) -> bool:
        """ ~ async method ~
        @Name:  initialize_data
        @Info:  This method checks for the correct data input to the xxxMESSAGE
                object. The expected datatypes for specific implementation is
                defined thru the static variable __valid_data_types__"""
        # Check for correct data types of the MESSAGE.data parameter
        if not isinstance(self.data, FunctionBaseCLASS):
            # This is meant only as a pre-check if the parameters are correct so you wouldn't eg. start
            # sending this message 6 hours later and only then realize the parameters were incorrect.
            # The parameters also get checked/parsed each period right before the send.

            # Convert any arguments passed into a list of arguments
            if isinstance(self.data, (list, tuple, set)):
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
        """ ~ async method ~
        @Name: initialize
        @Info:
            The initialize method initilizes the message object.
        @Params:
            options :: custom keyword arguments, this differes from inher. to inher. class that
                       is inherited from the BaseGUILD class and must be matched in the inherited class from BaseMESSAGE that
                       you want to use in that specific inherited class from BaseGUILD class"""
        if self.initialized:
            return True

        if not await self.initialize_channels(**options):
            return False

        if not await self.initialize_data():
            return False

        self.initialized = True
        return True

@sql.register_type("MessageTYPE")
class VoiceMESSAGE(BaseMESSAGE):
    """ ~ BaseMESSAGE class ~
    Name: VoiceMESSAGE
    Info: The VoiceMESSAGE object containts parameters which describe behaviour and data that will be sent to the channels.
    Params:
        Start Period , End Period (start_period, end_period) :: These 2 parameters specify the period on which the messages will be played:
            Start Period can be either:
                :: None :: Messages will be sent on intervals specified by End period,
                :: Integer >= 0 :: Messages will be sent on intervals randomly chosen between Start period and End period,
                                   where the randomly chosen intervals will be re::randomized after each sent message.
        Data (data) :: The data parameter is the actual data that will be sent using discord's API. The data types of this parameter can be:
                        - Path to an audio file (str)
                        - Function that accepts any amount of parameters and returns any of the above types.
                          To pass a function, YOU MUST USE THE framework.data_function decorator on the function before
                          passing the function to the framework.
        Channel IDs (channel_ids) :: List of IDs of all the channels you want data to be sent into.
        Start Now (start_now) :: A bool variable that can be either True or False. If True, then the framework will send the message
                                 as soon as it is run and then wait it's period before trying again. If False, then the message will
                                 not be sent immediatly after framework is ready, but will instead wait for the period to elapse."""

    __slots__ = (
        "randomized_time",
        "period",
        "random_range",
        "data",
        "channels",
        "timer",
        "force_retry",
    )

    __logname__ = "VoiceMESSAGE"
    __valid_data_types__ = {AUDIO}  # This is used in the BaseMESSAGE.initialize() to check if the passed data parameters are of correct type

    def __init__(self, start_period: Union[float, None],
                 end_period: float,
                 data: AUDIO,
                 channel_ids: Iterable[int],
                 start_now: bool = True):

        super().__init__(start_period, end_period, start_now)
        self.data = data
        self.channels = list(set(channel_ids)) # Auto remove duplicates

    def generate_log_context(self,
                             audio: AUDIO,
                             succeeded_ch: List[discord.VoiceChannel],
                             failed_ch: List[dict]):
        """ ~ method ~
        @Name: generate_log_context
        @Param:
            audio: AUDIO -- The audio that was streamed to the channels
            succeeded_ch: List[discord.VoiceChannel] -- list of the successfuly streamed channels,
            failed_ch: List[dict]   -- list of dictionaries contained the failed channel and the Exception
        @Info:
            Generates a dictionary containing data that will be saved in the message log"""

        succeeded_ch = [{"name": str(channel), "id" : channel.id} for channel in succeeded_ch]
        failed_ch = [{"name": str(entry["channel"]), "id" : entry["channel"].id,
                     "reason": str(entry["reason"])} for entry in failed_ch]
        return {
            "sent_data": {
                "streamed_audio" : audio.filename
            },
            "channels": {
                "successful" : succeeded_ch,
                "failed": failed_ch
            },
            "type" : type(self).__name__
        }

    def get_data(self) -> dict:
        """ ~ method ~
        @Name:  get_data
        @Info: Returns a dictionary of keyword arguments that is then expanded
               into other functions (send_channel, generate_log)"""
        data = None
        _data_to_send = {}
        data = self.data.get_data() if isinstance(self.data, FunctionBaseCLASS) else self.data
        if data is not None:
            if not isinstance(data, (list, tuple, set)):
                data = (data,)
            for element in data:
                if isinstance(element, AUDIO):
                    _data_to_send["audio"] = element
        return _data_to_send

    async def initialize_channels(self) -> bool:
        """ ~ async method ~
        @Name: initialize_channels
        @Info: This method initializes the implementation specific
               api objects and checks for the correct channel inpit context.
        @Return: Bool - True on success"""
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
                trace(f"VoiceMESSAGE object got ID ({channel_id}) for {type(channel).__name__}, but was expecting {discord.VoiceChannel.__name__}", TraceLEVELS.WARNING)
                self.channels.remove(channel)
            else:
                ch_i += 1

        return len(self.channels) > 0

    async def send_channel(self,
                           channel: discord.VoiceChannel,
                           audio: AUDIO) -> dict:
        """ ~ async method ~
        @Name : send_channel
        @Info:
            Streams audio to specific channel
        @Return:
        - dict:
            - "success" : bool ~ True if successful, else False
            - "reason"  : Exception ~ Only present if "success" is False,
                            contains the Exception returned by the send attempt."""
        stream = None
        voice_client = None
        try:
            # Check if client has permissions before attempting to join
            ch_perms = channel.permissions_for(channel.guild.get_member(client.get_client().user.id))
            if not all([ch_perms.connect, ch_perms.stream, ch_perms.speak]):
                raise self.generate_exception(403, 50013, "You lack permissions to perform that action", discord.Forbidden)

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
            if client.get_client().get_channel(channel.id) is None:
                ex = self.generate_exception(404, 10003, "Channel was deleted", discord.NotFound)
            else:
                ex = self.generate_exception(500, 0, "Timeout error", discord.HTTPException)
            return {"success": False, "reason": ex}
        finally:
            if stream is not None:
                stream.cleanup()
            if voice_client is not None:
                # Note (TODO): Should remove this in the future. Currently it disconnects instead moving to a different channel, because using
                #         .move_to(channel) method causes some sorts of "thread leak" (new threads keep getting created, waiting for pycord to fix this).
                await voice_client.disconnect()

    async def send(self) -> Union[dict,  None]:
        """" ~ async method ~
        @Name send
        @Info:
            Streams audio into the chanels
        @Return:
            Returns a dictionary generated by the generate_log_context method
            or the None object if message wasn't ready to be sent"""
        _data_to_send = self.get_data()
        if any(_data_to_send.values()):
            errored_channels = []
            succeded_channels= []

            for channel in self.channels:
                context = await self.send_channel(channel, **_data_to_send)
                if context["success"]:
                    succeded_channels.append(channel)
                else:
                    errored_channels.append({"channel":channel, "reason": context["reason"]})

            # Remove any channels that returned with code status 404 (They no longer exist)
            for data in errored_channels:
                reason = data["reason"]
                channel = data["channel"]
                if isinstance(reason, discord.HTTPException):
                    if (reason.status == 403 or
                        reason.code in {10003, 50013} # Unknown, Permissions
                    ):
                        self.channels.remove(channel)
                        trace(f"Channel {channel.name}(ID: {channel.id}) {'was deleted' if reason.code == 10003 else 'does not have permissions'}, removing it from the send list", TraceLEVELS.WARNING)

            return self.generate_log_context(**_data_to_send, succeeded_ch=succeded_channels, failed_ch=errored_channels)
        return None


@sql.register_type("MessageTYPE")
class TextMESSAGE(BaseMESSAGE):
    """ ~ BaseMESSAGE class ~
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
                        "edit" - each period the previously send message will be edited (if it exists)
                        or "clear-send" - previous message will be deleted and a new one sent.
    - Start Now (start_now) - A bool variable that can be either True or False. If True, then the framework will send the message
      as soon as it is run and then wait it's period before trying again. If False, then the message will not be sent immediatly after framework is ready,
      but will instead wait for the period to elapse."""
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
    __logname__ = "TextMESSAGE"
    __valid_data_types__ = {str, EMBED, FILE}

    def __init__(self, start_period: Union[float, None],
                 end_period: float,
                 data: Union[str, EMBED, FILE, List[Union[str, EMBED, FILE]]],
                 channel_ids: Iterable[int],
                 mode: Literal["send", "edit", "clear-send"] = "send",
                 start_now: bool = True):
        super().__init__(start_period, end_period, start_now)
        self.data = data
        self.mode = mode
        self.channels = list(set(channel_ids)) # Automatically removes duplicates
        self.sent_messages = {ch_id : None for ch_id in channel_ids} # Dictionary for storing last sent message for each channel

    def generate_log_context(self,
                             text : str,
                             embed : EMBED,
                             files : List[FILE],
                             succeeded_ch: List[Union[discord.TextChannel, discord.Thread]],
                             failed_ch: List[dict]):
        """ ~ method ~
        @Name : generate_log_context
        @Param:
            text : str -- The text that was sent
            embed : EMBED  -- The embed that was sent
            files : List[FILE] -- List of files that were sent
            succeeded_ch: List[discord.VoiceChannel] -- list of the successfuly streamed channels,
            failed_ch: List[dict]   -- list of dictionaries contained the failed channel and the Exception
        @Info:
            Generates a dictionary containing data that will be saved in the message log"""

        succeeded_ch = [{"name": str(channel), "id" : channel.id} for channel in succeeded_ch]
        failed_ch = [{"name": str(entry["channel"]), "id" : entry["channel"].id,
                     "reason": str(entry["reason"])} for entry in failed_ch]

        embed = embed.to_dict() if embed is not None else None

        files = [x.filename for x in files]
        sent_data_context = {}
        if text is not None:
            sent_data_context["text"] = text
        if embed is not None:
            sent_data_context["embed"] = embed
        if len(files):
            sent_data_context["files"] = files
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
    
    def get_data(self) -> dict:
        """ ~ method ~
        @Name:  get_data
        @Info: Returns a dictionary of keyword arguments that is then expanded
               into other functions (send_channel, generate_log)"""
        data = self.data.get_data() if isinstance(self.data, FunctionBaseCLASS) else self.data
        _data_to_send = {"embed": None, "text": None, "files": []}
        if data is not None:
            if not isinstance(data, (list, tuple, set)):
                data = (data,)
            for element in data:
                if isinstance(element, str):
                    _data_to_send["text"] = element
                elif isinstance(element, EMBED):
                    _data_to_send["embed"] = element
                elif isinstance(element, FILE):
                    _data_to_send["files"].append(element)
        return _data_to_send

    async def initialize_channels(self) -> bool:
        """ ~ async method ~
        @Name: initialize_channels
        @Info: This method initializes the implementation specific
               api objects and checks for the correct channel inpit context.
        @Return: Bool - True on success"""
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
                trace(f"TextMESSAGE object got ID ({channel_id}) for {type(channel).__name__}, but was expecting {discord.TextChannel.__name__}", TraceLEVELS.WARNING)
                self.channels.remove(channel)
            else:
                ch_i += 1

        return len(self.channels) > 0
    
    async def handle_error(self, channel: Union[discord.TextChannel, discord.Thread], ex: Exception):
        """ ~ async method ~
        @Name: handle_error
        @Info: This method handles the error that occured during the execution of the function.
        @Param:
            ex : Exception -- The exception that occured
        @Return: Bool - True on success"""
        handled = False
        if isinstance(ex, discord.HTTPException):
            if ex.status == 429:  # Rate limit
                retry_after = int(ex.response.headers["Retry-After"]) * RLIM_SAFETY_FACTOR
                if ex.code == 20016:    # Slow Mode
                    self.force_retry["ENABLED"] = True
                    self.force_retry["TIME"] = retry_after
                    trace(f"{channel.name} is in slow mode, retrying in {retry_after} seconds", TraceLEVELS.WARNING)
                handled = True
            elif ex.status == 404:      # Unknown object
                if ex.code == 10008:    # Unknown message
                    self.sent_messages[channel.id]  = None
                    handled = True
        return handled

    async def send_channel(self,
                           channel: discord.TextChannel,
                           text: str,
                           embed: EMBED,
                           files: List[FILE]) -> dict:
        """ ~ async method ~
        @Name : send_channel
        @Info:
            Sends data to specific channel.
        @Return:
        - dict:
            - "success" : bool ~ True if successful, else False
            - "reason"  : Exception ~ Only present if "success" is False,
                            contains the Exception returned by the send attempt."""

        ch_perms = channel.permissions_for(channel.guild.get_member(client.get_client().user.id))
        for tries in range(3):  # Maximum 3 tries (if rate limit)
            try:
                if ch_perms.send_messages is False: # Check if we have permissions
                    raise self.generate_exception(403, 50013, "You lack permissions to perform that action", discord.Forbidden)

                # Delete previous message if clear-send mode is choosen and message exists
                if self.mode == "clear-send" and self.sent_messages[channel.id] is not None:
                    await self.sent_messages[channel.id].delete()
                    self.sent_messages[channel.id] = None

                # Send/Edit message
                if  (self.mode in  {"send" , "clear-send"} or # Mode dictates to send new message or delete previous and then send new message or mode dictates edit but message was  never sent to this channel before
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
                if not await self.handle_error(channel, ex):
                    return {"success" : False, "reason" : ex}

    async def send(self) -> Union[dict,  None]:
        """"~ async method ~
        @Name: send
        @Info:
            Sends the data into the channels
        @Return:
            Returns a dictionary generated by the generate_log_context method
            or the None object if message wasn't ready to be sent"""
        data_to_send = self.get_data()
        if any(data_to_send.values()):
            errored_channels = []
            succeded_channels= []

            # Send to channels
            for channel in self.channels:
                # Clear previous messages sent to channel if mode is MODE_DELETE_SEND
                if GLOBALS.is_user:
                    await asyncio.sleep(RLIM_USER_WAIT_TIME)
                context = await self.send_channel(channel, **data_to_send)
                if context["success"]:
                    succeded_channels.append(channel)
                else:
                    errored_channels.append({"channel":channel, "reason": context["reason"]})

            # Remove any channels that returned with code status 404 (They no longer exist)
            for data in errored_channels:
                reason = data["reason"]
                channel = data["channel"]
                if isinstance(reason, discord.HTTPException):
                    if (reason.status == 403 or                    # Forbidden
                        reason.code in {50007, 10003}     # Not Forbidden, but bad error codes
                    ):
                        self.channels.remove(channel)
                        trace(f"Channel {channel.name}(ID: {channel.id}) {'was deleted' if reason.code == 10003 else 'does not have permissions'}, removing it from the send list", TraceLEVELS.WARNING)

            # Return sent data + failed and successful function for logging purposes
            return self.generate_log_context(**data_to_send, succeeded_ch=succeded_channels, failed_ch=errored_channels)

        return None


@sql.register_type("MessageTYPE")
class DirectMESSAGE(BaseMESSAGE):
    """ ~ BaseMESSAGE class ~
    @Name: DirectMESSAGE
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
        Dictates if the message should be sent immediatly after framework start or if it should wait it's period first and then send"""

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
    __logname__ = "DirectMESSAGE"
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
                             text : str,
                             embed : EMBED,
                             files : List[FILE],
                             **success_context):

        """ ~ method ~
        @Name: generate_log_context
        @Param:
            text : str -- The text that was sent
            embed : EMBED  -- The embed that was sent
            files : List[FILE] -- List of files that were sent
            succeeded_ch: List[discord.VoiceChannel] -- list of the successfuly streamed channels,
            failed_ch: List[dict]   -- list of dictionaries contained the failed channel and the Exception
        @Info:
            Generates a dictionary containing data that will be saved in the message log"""

        embed = embed.to_dict() if embed is not None else None
        files = [x.filename for x in files]
        if not success_context["success"]:
            success_context["reason"] = str(success_context["reason"])
        sent_data_context = {}
        if text is not None:
            sent_data_context["text"] = text
        if embed is not None:
            sent_data_context["embed"] = embed
        if len(files):
            sent_data_context["files"] = files
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

    def get_data(self) -> dict:
        """ ~ method ~
        @Name:  get_data
        @Info: Returns a dictionary of keyword arguments that is then expanded
               into other functions (send_channel, generate_log).
               This is exactly the same as in TextMESSAGE"""
        return TextMESSAGE.get_data(self)

    async def initialize_channels(self,
                                  user: discord.User) -> bool:
        """ ~ async method ~
        @Name: initialize_channels
        @Info:
        The method creates a direct message channel and
        returns True on success or False on failure
        @Parameters:
        - options ~ dictionary containing key with user_id
                    (sent to by the USER instance's initialize method)"""
        try:
            self.dm_channel = user.dm_channel if user.dm_channel is not None else await user.create_dm()
            if self.dm_channel is None:
                return False
        except discord.HTTPException as ex:
            return False
        return True

    async def handle_error(self, ex: Exception):
        """ ~ async method ~
        @Name: handle_error
        @Info:
        The method handles the error that occured during the send_channel method.
        @Parameters:
        - ex ~ Exception instance"""
        handled = False
        if isinstance(ex, discord.HTTPException):
            if ex.status == 429 or ex.code == 40003: # Too Many Requests or opening DMs too fast
                retry_after = float(ex.response.headers["Retry-After"])  * RLIM_SAFETY_FACTOR
                trace(f"Rate limited, sleeping for {retry_after} seconds", TraceLEVELS.WARNING)
                await asyncio.sleep(retry_after)
                handled = True
            elif ex.status == 404:      # Unknown object
                if ex.code == 10008:    # Unknown message
                    self.previous_message  = None
                    handled = True
            elif ex.status == 400: # Bad Request
                await asyncio.sleep(RLIM_USER_WAIT_TIME * 5) # To avoid triggering selfbot detection

        return handled

    async def send_channel(self,
                           text: str,
                           embed: EMBED,
                           files: List[FILE]) -> dict:
        """ ~ async method ~
        @Name : send_channel
        @Info:
        Sends data to the DM channel (user).
        @Return:
        - dict:
            - "success" : bool ~ True if successful, else False
            - "reason"  : Exception ~ Only present if "success" is False,
                            contains the Exception returned by the send attempt."""
        # Send/Edit messages
        for tries in range(3):  # Maximum 3 tries (if rate limit)
            try:
                # Deletes previous message if it exists and mode is "clear-send"
                if self.mode == "clear-send" and self.previous_message is not None:
                    self.previous_message.delete()
                    self.previous_message = None

                # Sends a new message
                if (self.mode in {"send" , "clear-send"} or
                     self.mode == "edit" and self.previous_message is None
                ):
                    self.previous_message = await self.dm_channel.send(text, embed=embed,
                                                                       files=[discord.File(fwFILE.filename) for fwFILE in files])

                # Mode is edit and message was already send to this channel
                elif self.mode == "edit":
                    await self.previous_message.edit(text, embed=embed)
                return {"success" : True}

            except Exception as ex:
                if await self.handle_error(ex) is False or tries == 2:
                    return {"success" : False, "reason" : ex}

    async def send(self) -> Union[dict, None]:
        """" ~ async method ~
        @Name: send
        @Info:
            Sends the data into the DM channel of the user.
        @Return:
            Returns a dictionary generated by the generate_log_context method
            or the None object if message wasn't ready to be sent"""
        # Parse data from the data parameter
        data_to_send = self.get_data()
        if any(data_to_send.values()):
            if GLOBALS.is_user:
                await asyncio.sleep(RLIM_USER_WAIT_TIME)
            context = await self.send_channel(**data_to_send)
            if context["success"] is False:
                reason  = context["reason"]
                if isinstance(reason, discord.HTTPException):
                    if (reason.status == 403 or                    # Forbidden
                        reason.code in {50007, 10001, 10003}     # Not Forbidden, but bad error codes
                    ):
                        self.dm_channel = None

            return self.generate_log_context(**data_to_send, **context)

        return None


async def initialize(is_user: bool) -> bool:
    """ ~ async function ~
    @Name: initialize
    @Info:
        Initializes the module.
    @Parameters:
        - is_user: bool ~ True if the class is used for a user, else False"""
    GLOBALS.is_user = is_user
    return True