"""~  text message related ~
@Info:
    Contains definitions for message classes that are text based (TextMESSAGE & DirectMESSAGE)."""

from   .base        import *
from   ..           import client
from   ..           import sql
from   ..dtypes     import *
from   ..tracing    import *
from   ..const      import *
from   ..exceptions import *
from   ..           import core
from   typing       import List, Iterable, Union, Literal
import asyncio
import _discord as discord


__all__ = (
    "TextMESSAGE",
    "DirectMESSAGE"
)


@sql.register_type("MessageTYPE")
class TextMESSAGE(BaseMESSAGE):
    """ ~ class ~
    - @Info: The TextMESSAGE object containts parameters which describe behaviour and data that will be sent to the channels.
    - @Params:
        - start_period, end_period ~ These 2 parameters specify the period on which the messages will be sent.
            - start_period can be either:
                - None ~ Messages will be sent on intervals specified by End period,
                - Integer >= 0 ~ Messages will be sent on intervals randomly chosen between Start period and End period,
                             where the randomly chosen intervals will be re-randomized after each sent message.
        - (data ~ The data parameter is the actual data that will be sent using discord's API. The data types of this parameter can be:
            - str (normal text),
            - framework.EMBED,
            - framework.FILE,
            - List/Tuple containing any of the above arguments (There can up to 1 string, up to 1 embed and up to 10 framework.FILE objects,
            if more than 1 string or embeds are sent, the framework will only consider the last found).
            - Function that accepts any amount of parameters and returns any of the above types.
            To pass a function, YOU MUST USE THE framework.data_function decorator on the function before passing the function to the framework.
        - channels ~ List of IDs of all the channels you want data to be sent into.
        - mode ~ Parameter that defines how message will be sent to a channel. It can be "send" - each period a new message will be sent,
                            "edit" - each period the previously send message will be edited (if it exists)
                            or "clear-send" - previous message will be deleted and a new one sent.
        - start_now ~ A bool variable that can be either True or False. If True, then the framework will send the message
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
                 channels: Iterable[int],
                 mode: Literal["send", "edit", "clear-send"] = "send",
                 start_now: bool = True):
        super().__init__(start_period, end_period, start_now)
        self.data = data
        self.mode = mode
        self.channels = list(set(channels)) # Automatically removes duplicates
        self.sent_messages = {ch_id : None for ch_id in channels} # Dictionary for storing last sent message for each channel

    def generate_log_context(self,
                             text : str,
                             embed : EMBED,
                             files : List[FILE],
                             succeeded_ch: List[Union[discord.TextChannel, discord.Thread]],
                             failed_ch: List[dict]):
        """ ~ method ~
        - @Name : generate_log_context
        - @Param:
            - text ~ The text that was sent
            - embed ~ The embed that was sent
            - files ~ List of files that were sent
            - succeeded_ch: ~ list of the successfuly streamed channels,
            - failed_ch: ~ list of dictionaries contained the failed channel and the Exception object
        - @Info: Generates a dictionary containing data that will be saved in the message log"""

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

    async def initialize_channels(self):
        """ ~ async method ~
        - @Name: initialize_channels
        - @Info: This method initializes the implementation specific
                 api objects and checks for the correct channel inpit context.
        - @Exceptions:
            - <DAFInvalidParameterError code=DAF_INVALID_TYPE> ~ Raised when the object retrieved from channels is not a discord.TextChannel or discord.Thread object.
            - <DAFMissingParameterError code=DAF_MISSING_PARAMETER> ~ Raised when no valid channels were parsed."""
        ch_i = 0
        cl = client.get_client()
        while ch_i < len(self.channels):
            channel = self.channels[ch_i]
            if isinstance(channel, discord.abc.GuildChannel):
                channel_id = channel.id
            else:
                channel_id = channel
                channel = self.channels[ch_i] = cl.get_channel(channel_id)

            if channel is None:
                trace(f"Unable to get channel from ID {channel_id}", TraceLEVELS.ERROR)
                self.channels.remove(channel)
            elif type(channel) not in {discord.TextChannel, discord.Thread}:
                raise DAFInvalidParameterError(f"TextMESSAGE object received channel type of {type(channel).__name__}, but was expecting discord.TextChannel or discord.Thread", DAF_INVALID_TYPE)
            else:
                ch_i += 1

        if not len(self.channels):
            raise DAFMissingParameterError(f"No valid channels were passed to {type(self)} object", DAF_MISSING_PARAMETER)
    
    async def handle_error(self, channel: Union[discord.TextChannel, discord.Thread], ex: Exception) -> bool:
        """ ~ async method ~
        - @Name: handle_error
        - @Info: This method handles the error that occured during the execution of the function.
        - @Param:
            - ex ~ The exception that occured
        - @Return ~ Returns True on successful handling"""
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
        - @Name : send_channel
        - @Info: Sends data to specific channel.
        - @Return:
            - dict:
                - "success" ~ Returns True if successful, else False
                - "reason"  ~ Only present if "success" is False,
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
        """" ~ async method ~
        - @Name: send
        - @Info: Sends the data into the channels
        - @Return:
            Returns a dictionary generated by the generate_log_context method
            or the None object if message wasn't ready to be sent (data_function returned None or an invalid type)"""
        data_to_send = self.get_data()
        if any(data_to_send.values()):
            errored_channels = []
            succeded_channels= []

            # Send to channels
            for channel in self.channels:
                # Clear previous messages sent to channel if mode is MODE_DELETE_SEND
                if core.GLOBALS.is_user:
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
    """ ~ class ~
    - @Name: DirectMESSAGE
    - @Info: DirectMESSAGE represents a message that will be sent into direct messages
    - @Params:
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
        - @Name: generate_log_context
        - @Param:
            - text ~ The text that was sent
            - embed ~ The embed that was sent
            - files ~ List of files that were sent
            - succeeded_ch ~ list of the successfuly streamed channels,
            - failed_ch ~ list of dictionaries contained the failed channel and the Exception
        - @Info: Generates a dictionary containing data that will be saved in the message log"""

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
        - @Name: get_data
        - @Info: Returns a dictionary of keyword arguments that is then expanded
                 into other functions (send_channel, generate_log).
                 This is exactly the same as in TextMESSAGE"""
        return TextMESSAGE.get_data(self)

    async def initialize_channels(self,
                                  user: discord.User):
        """ ~ async method ~
        - @Name: initialize_channels
        - @Info:
            The method creates a direct message channel and
            returns True on success or False on failure
        - @Parameters:
            - user ~ discord User object to whom the DM will be created for
        - @Exceptions:
            - <DAFInitError code=DAF_USER_CREATE_DM> ~ Raised when the direct message channel could not be created"""
        try:
            self.dm_channel = await user.create_dm()
        except discord.HTTPException as ex:
            raise DAFInitError(f"Unable to create DM with user {user.display_name}", DAF_USER_CREATE_DM)

    async def handle_error(self, ex: Exception) -> bool:
        """ ~ async method ~
        - @Name: handle_error
        - @Info: The method handles the error that occured during the send_channel method.
        - @Parameters:
            - ex ~ Exception instance
        - @Return: True if the error was handled, False if not"""
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
        - @Name : send_channel
        - @Info:  Sends data to the DM channel (user).
        - @Return:
            - dict:
                - "success" ~ True if successful, else False
                - "reason"  ~ Only present if "success" is False,
                              contains the Exception returned by the send attempt."""
        # Send/Edit messages
        for tries in range(3):  # Maximum 3 tries (if rate limit)
            try:
                # Deletes previous message if it exists and mode is "clear-send"
                if self.mode == "clear-send" and self.previous_message is not None:
                    await self.previous_message.delete()
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
        - @Name: send
        - @Info: Sends the data into the DM channel of the user.
        - @Return:
            Returns a dictionary generated by the generate_log_context method
            or the None object if message wasn't ready to be sent (data_function returned None)"""
        # Parse data from the data parameter
        data_to_send = self.get_data()
        if any(data_to_send.values()):
            if core.GLOBALS.is_user:
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
