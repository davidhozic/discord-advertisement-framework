"""
Contains definitions for message classes that are text based."""

from typing import Any, Dict, List, Iterable, Optional, Union, Literal
from datetime import datetime, timedelta
from typeguard import typechecked

from .base import *
from ..dtypes import *
from ..logging.tracing import *

from .. import client
from ..logging import sql
from .. import misc

import asyncio
import _discord as discord


__all__ = (
    "TextMESSAGE",
    "DirectMESSAGE"
)

# Configuration
# ---------------------------
RLIM_USER_WAIT_TIME = 20

# Type aliases
# ---------------------------
TMDataType = Union[str, EMBED, discord.Embed, FILE, Iterable[Union[str, EMBED, discord.Embed, FILE]], _FunctionBaseCLASS]

# Register message modes
sql.register_type("MessageMODE", "send")
sql.register_type("MessageMODE", "edit")
sql.register_type("MessageMODE", "clear-send")

@misc.doc_category("Messages", path="message")
@sql.register_type("MessageTYPE")
class TextMESSAGE(BaseMESSAGE):
    """
    This class is used for creating objects that represent messages which will be sent to Discord's TEXT CHANNELS.

    .. versionchanged:: v2.3

        :Slow mode period handling:

            When the period is lower than the remaining time, the framework will start
            incrementing the original period by original period until it is larger then
            the slow mode remaining time.

    Parameters
    ------------
    start_period: Union[int, timedelta, None]
        The value of this parameter can be:

        - None - Use this value for a fixed (not randomized) sending period
        - timedelta object - object describing time difference, if this is used, then the parameter represents the bottom limit of the **randomized** sending period.
    end_period: Union[int, timedelta]
        If ``start_period`` is not None, then this represents the upper limit of randomized time period in which messages will be sent.
        If ``start_period`` is None, then this represents the actual time period between each message send.

        .. CAUTION::
            When the period is lower than the remaining time, the framework will start
            incrementing the original period by original period until it is larger then
            the slow mode remaining time.

        .. code-block:: python
            :caption: **Randomized** sending period between **5** seconds and **10** seconds.

            # Time between each send is somewhere between 5 seconds and 10 seconds.
            daf.TextMESSAGE(start_period=timedelta(seconds=5), end_period=timedelta(seconds=10), data="Second Message", channels=[12345], mode="send", start_in=timedelta(seconds=0))

        .. code-block:: python
            :caption: **Fixed** sending period at **10** seconds

            # Time between each send is exactly 10 seconds.
            daf.TextMESSAGE(start_period=None, end_period=timedelta(seconds=10), data="Second Message", channels=[12345], mode="send", start_in=timedelta(seconds=0))
    data: Union[str, discord.Embed, FILE, List[Union[str, discord.Embed, FILE]], _FunctionBaseCLASS]
        The data parameter is the actual data that will be sent using discord's API. The data types of this parameter can be:
            - str (normal text),
            - :class:`discord.Embed`,
            - :ref:`FILE`,
            - List/Tuple containing any of the above arguments (There can up to 1 string, up to 1 :class:`discord.Embed` and up to 10 :ref:`FILE` objects. If more than 1 string or embeds are sent, the framework will only consider the last found).
            - Function that accepts any amount of parameters and returns any of the above types. To pass a function, YOU MUST USE THE :ref:`data_function` decorator on the function before passing the function to the daf.
    channels: Union[Iterable[Union[int, discord.TextChannel, discord.Thread]], daf.message.AutoCHANNEL]
        .. versionchanged:: v2.3
            Can also be :class:`~daf.message.AutoCHANNEL`

        Channels that it will be advertised into (Can be snowflake ID or channel objects from PyCord).
    mode: Optional[str]
        Parameter that defines how message will be sent to a channel.
        It can be:

        - "send" -    each period a new message will be sent,
        - "edit" -    each period the previously send message will be edited (if it exists)
        - "clear-send" -    previous message will be deleted and a new one sent.
    start_in: Optional[timedelta]
        When should the message be first sent.
    remove_after: Optional[Union[int, timedelta, datetime]]
        Deletes the message after:

        * int - provided amounts of sends
        * timedelta - the specified time difference
        * datetime - specific date & time
    """

    __slots__ = (
        "channels",
        "mode",
        "sent_messages",
    )

    @typechecked
    def __init__(self, 
                 start_period: Union[int, timedelta, None],
                 end_period: Union[int, timedelta],
                 data: TMDataType,
                 channels: Union[Iterable[Union[int, discord.TextChannel, discord.Thread]], AutoCHANNEL],
                 mode: Optional[Literal["send", "edit", "clear-send"]] = "send",
                 start_in: Optional[Union[timedelta, bool]]=timedelta(seconds=0),
                 remove_after: Optional[Union[int, timedelta, datetime]]=None):
        super().__init__(start_period, end_period, data, start_in, remove_after)
        self.mode = mode
        self.channels = channels
        self.sent_messages = {} # Dictionary for storing last sent message for each channel
    
    def _check_state(self) -> bool:
        """
        Checks if the message is ready to be deleted.
        
        Returns
        ----------
        True
            The message should be deleted.
        False
            The message is in proper state, do not delete.
        """
        return super()._check_state() or not bool(self.channels)
   
    def _update_state(self, err_channels: List[dict]):
        "Updates the state of the object based on errored channels."
        super()._update_state()
        # Remove any channels that returned with code status 404 (They no longer exist)
        for data in err_channels:
            reason = data["reason"]
            channel = data["channel"]
            if isinstance(reason, discord.HTTPException):
                if (reason.status == 403 or                    # Forbidden
                    reason.code in {50007, 10003}):     # Not Forbidden, but bad error codes
                    self.channels.remove(channel)

    def _check_period(self, slowmode_delay: timedelta):
        """
        Helper function used for checking the the period is lower
        than the slow mode delay.

        .. versionadded:: v2.3

        Parameters
        --------------
        slowmode_delay: timedelta
            The (maximum) slowmode delay.
        """
        if self.start_period is not None:
            if self.start_period < slowmode_delay:
                    self.start_period, self.end_period = slowmode_delay, slowmode_delay + self.end_period - self.start_period
        elif self.end_period < slowmode_delay:
            self.end_period = slowmode_delay

    def generate_log_context(self,
                             text: Optional[str],
                             embed: Union[discord.Embed, EMBED],
                             files: List[FILE],
                             succeeded_ch: List[Union[discord.TextChannel, discord.Thread]],
                             failed_ch: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generates information about the message send attempt that is to be saved into a log.

        Parameters
        -----------
        text: str
            The text that was sent.
        embed: discord.Embed
            The embed that was sent.
        files: List[FILE]
            List of files that were sent.
        succeeded_ch: List[Union[discord.TextChannel, discord.Thread]]
            List of the successfully streamed channels.
        failed_ch: failed_ch: List[Dict[Union[discord.TextChannel, discord.Thread], Exception]]
            List of dictionaries contained the failed channel and the Exception object.

        Returns
        ----------
        Dict[str, Any]
            .. code-block:: python
                
                {
                    sent_data:
                    {
                        text: str - The text that was sent,
                        embed: Dict[str, Any] - The embed that was sent,
                        files: List[str] - List of files that were sent
                    },
                    
                    channels:
                    {
                        successful:
                        {
                            id: int - Snowflake id,
                            name: str - Channel name
                        },
                        failed:
                        {
                            id: int - Snowflake id,
                            name: str - Channel name,
                            reason: str - Exception that caused the error
                        }
                    },
                    type: str - The type of the message, this is always TextMESSAGE,
                    mode: str - The mode used to send the message (send, edit, clear-send)
                }
        """
        if not (len(succeeded_ch) + len(failed_ch)):
            return None

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

    async def _get_data(self) -> dict:
        """"
        Returns a dictionary of keyword arguments that is then expanded
        into other methods eg. `_send_channel, _generate_log`.

        .. versionchanged:: v2.3
            Turned async.
        """
        data = await super()._get_data()
        _data_to_send = {"embed": None, "text": None, "files": []}
        if data is not None:
            if not isinstance(data, (list, tuple, set)):
                data = (data,)
            for element in data:
                if isinstance(element, str):
                    _data_to_send["text"] = element
                elif isinstance(element, (EMBED, discord.Embed)):
                    _data_to_send["embed"] = element
                elif isinstance(element, FILE):
                    _data_to_send["files"].append(element)
        return _data_to_send

    async def initialize(self, parent: Any):
        """
        This method initializes the implementation specific api objects and checks for the correct channel input context.

        Parameters
        --------------
        parent: daf.guild.GUILD
            The GUILD this message is in

        Raises
        ------------
        TypeError
            Channel contains invalid channels
        ValueError
            Channel does not belong to the guild this message is in.
        ValueError
            No valid channels were passed to object"
        """
        ch_i = 0
        self.parent = parent
        cl = parent.parent.client
        _guild = parent.apiobject
        to_remove = []

        if isinstance(self.channels, AutoCHANNEL):
            await self.channels.initialize(self, "text_channels")
        else:
            for ch_i, channel in enumerate(self.channels):
                if isinstance(channel, discord.abc.GuildChannel):
                    channel_id = channel.id
                else:
                    # Snowflake IDs provided
                    channel_id = channel
                    channel = self.channels[ch_i] = cl.get_channel(channel_id)

                if channel is None:
                    trace(f"Unable to get channel from ID {channel_id}", TraceLEVELS.WARNING)
                    to_remove.append(channel)
                elif type(channel) not in {discord.TextChannel, discord.Thread}:
                    raise TypeError(f"TextMESSAGE object received channel type of {type(channel).__name__}, but was expecting discord.TextChannel or discord.Thread")
                elif channel.guild != _guild:
                    raise ValueError(f"The channel {channel.name}(ID: {channel_id}) does not belong into {_guild.name}(ID: {_guild.id}) but is part of {channel.guild.name}(ID: {channel.guild.id})")
            
            for channel in to_remove:
                self.channels.remove(channel)

            if not self.channels:
                raise ValueError(f"No valid channels were passed to {self} object")

            # Increase period to slow mode delay if it is lower
            slowmode_delay = timedelta(seconds=max(channel.slowmode_delay for channel in self.channels))
            self._check_period(slowmode_delay)
    
    async def _handle_error(self, channel: Union[discord.TextChannel, discord.Thread], ex: Exception) -> bool:
        """
        This method handles the error that occurred during the execution of the function.
        Returns `True` if error was handled.

        Slow mode period handling:
        When the period is lower than the remaining time, the framework will start
        incrementing the original period by original period until it is larger then
        the slow mode remaining time.

        Parameters
        -----------
        channel: Union[discord.TextChannel, discord.Thread]
            The channel where the exception occurred.
        ex: Exception
            The exception that occurred during a send attempt.
        """
        handled = False
        if isinstance(ex, discord.HTTPException):
            if ex.status == 429:  # Rate limit
                retry_after = int(ex.response.headers["Retry-After"]) + 1
                if ex.code == 20016:    # Slow Mode
                    self.next_send_time = datetime.now() + timedelta(seconds=retry_after)
                    trace(f"{channel.name} is in slow mode, retrying in {retry_after} seconds", TraceLEVELS.WARNING)
                    slowmode_delay = timedelta(seconds=channel.slowmode_delay)
                    self._check_period(slowmode_delay) # Fix the period

            elif ex.status == 404:      # Unknown object
                if ex.code == 10008:    # Unknown message
                    self.sent_messages[channel.id] = None
                    handled = True

        return handled

    async def _send_channel(self,
                           channel: Union[discord.TextChannel, discord.Thread, None],
                           text: Optional[str],
                           embed: Optional[Union[discord.Embed, EMBED]],
                           files: List[FILE]) -> dict:
        """
        Sends data to specific channel

        Returns a dictionary:
        - "success" - Returns True if successful, else False
        - "reason"  - Only present if "success" is False, contains the Exception returned by the send attempt

        Parameters
        -------------
        channel: Union[discord.TextChannel, discord.Thread]
            The channel in which to send the data.
        text: str
            The text to send.
        embed: discord.Embed
            The embedded frame to send.
        files: List[FILE]
            List of files to send.
        """
        # Check if client has permissions before attempting to join
        for tries in range(3):  # Maximum 3 tries (if rate limit)
            try:
                # Check if we have permissions
                client_: discord.Client = self.parent.parent.client
                if (member := channel.guild.get_member(client_.user.id)) is None:
                    raise self._generate_exception(404, -1, "Client user could not be found in guild members", discord.NotFound)

                if channel.guild.me.pending:
                    raise self._generate_exception(
                        403, 50009,
                        "Channel verification level is too high for you to gain access",
                        discord.Forbidden
                    )

                ch_perms = channel.permissions_for(member)
                if ch_perms.send_messages is False:
                    raise self._generate_exception(403, 50013, "You lack permissions to perform that action", discord.Forbidden)

                # Check if channel still exists in cache (has not been deleted)
                if self.parent.parent.client.get_channel(channel.id) is None:
                    raise self._generate_exception(404, 10003, "Channel was deleted", discord.NotFound)

                # Delete previous message if clear-send mode is chosen and message exists
                if self.mode == "clear-send" and self.sent_messages.get(channel.id, None) is not None:
                    await self.sent_messages[channel.id].delete()
                    self.sent_messages[channel.id] = None

                # Send/Edit message
                if (self.mode in {"send" , "clear-send"} or # Mode dictates to send new message or delete previous and then send new message or mode dictates edit but message was  never sent to this channel before
                    self.mode == "edit" and self.sent_messages.get(channel.id, None) is None
                ):
                    self.sent_messages[channel.id] = await channel.send(  text,
                                                            embed=embed,
                                                            # Create discord.File objects here so it is catched by the except block and then logged
                                                            files=[discord.File(fwFILE.filename) for fwFILE in files])
                # Mode is edit and message was already send to this channel
                elif self.mode == "edit":
                    await self.sent_messages[channel.id].edit ( text,
                                                                embed=embed)

                return {"success" : True}

            except Exception as ex:
                if not await self._handle_error(channel, ex):
                    return {"success" : False, "reason" : ex}

    @misc._async_safe("update_semaphore")
    async def _send(self) -> Union[dict, None]:
        """
        Sends the data into the channels.

        Returns
        ----------
        Union[Dict, None]
            Returns a dictionary generated by the ``generate_log_context`` method or the None object if message wasn't ready to be sent (:ref:`data_function` returned None or an invalid type)

            This is then passed to :ref:`GUILD`._generate_log method.
        """
        # Acquire mutex to prevent update method from writing while sending
        data_to_send = await self._get_data()
        if any(data_to_send.values()):
            errored_channels = []
            succeeded_channels= []

            # Send to channels
            for channel in self.channels:
                # Clear previous messages sent to channel if mode is MODE_DELETE_SEND
                context = await self._send_channel(channel, **data_to_send)
                if context["success"]:
                    succeeded_channels.append(channel)
                else:
                    errored_channels.append({"channel":channel, "reason": context["reason"]})

            self._update_state(errored_channels)
            return self.generate_log_context(**data_to_send, succeeded_ch=succeeded_channels, failed_ch=errored_channels) # Return sent data + failed and successful function for logging purposes

        return None

    @typechecked
    @misc._async_safe("update_semaphore")
    async def update(self, _init_options: Optional[dict] = {}, **kwargs: Any):
        """
        .. versionadded:: v2.0

        Used for changing the initialization parameters the object was initialized with.

        .. warning::
            Upon updating, the internal state of objects get's reset, meaning you basically have a brand new created object.

        Parameters
        -------------
        **kwargs: Any
            Custom number of keyword parameters which you want to update, these can be anything that is available during the object creation.

        Raises
        -----------
        TypeError
            Invalid keyword argument was passed
        Other
            Raised from .initialize() method.
        """
        if "start_in" not in kwargs:
            # This parameter does not appear as attribute, manual setting necessary
            kwargs["start_in"] = timedelta(seconds=0)
        
        if "data" not in kwargs:
            kwargs["data"] = self._data

        if "channels" not in kwargs and not isinstance(self.channels, AutoCHANNEL):
            kwargs["channels"] = [x.id for x in self.channels]
        
        if not len(_init_options):
            _init_options = {"parent": self.parent}

        await misc._update(self, init_options=_init_options, **kwargs) # No additional modifications are required
        
        if isinstance(self.channels, AutoCHANNEL):
            await self.channels.update()


@misc.doc_category("Messages", path="message")
@sql.register_type("MessageTYPE")
class DirectMESSAGE(BaseMESSAGE):
    """
    This class is used for creating objects that represent messages which will be sent to Discord's TEXT CHANNELS.

    .. deprecated:: v2.1

        - start_in (start_now) - Using bool value to dictate whether the message should be sent at framework start.
        - start_period, end_period - Using int values, use ``timedelta`` object instead.
    
    .. versionchanged:: v2.1

        - start_period, end_period Accept timedelta objects.
        - start_now - renamed into ``start_in`` which describes when the message should be first sent.
        - removed ``deleted`` property

    Parameters
    ------------
    start_period: Union[int, timedelta, None]
        The value of this parameter can be:

        - None - Use this value for a fixed (not randomized) sending period
        - timedelta object - object describing time difference, if this is used, then the parameter represents the bottom limit of the **randomized** sending period.

    end_period: Union[int, timedelta]
        If ``start_period`` is not None, then this represents the upper limit of randomized time period in which messages will be sent.
        If ``start_period`` is None, then this represents the actual time period between each message send.

        .. code-block:: python
            :caption: **Randomized** sending period between **5** seconds and **10** seconds.

            # Time between each send is somewhere between 5 seconds and 10 seconds.
            daf.DirectMESSAGE(start_period=timedelta(seconds=5), end_period=timedelta(seconds=10), data="Second Message",  mode="send", start_in=timedelta(seconds=0))

        .. code-block:: python
            :caption: **Fixed** sending period at **10** seconds

            # Time between each send is exactly 10 seconds.
            daf.DirectMESSAGE(start_period=None, end_period=timedelta(seconds=10), data="Second Message",  mode="send", start_in=timedelta(seconds=0))

    data: Union[str, discord.Embed FILE, List[Union[str, discord.Embed, FILE]], _FunctionBaseCLASS]
        The data parameter is the actual data that will be sent using discord's API. The data types of this parameter can be:
            - str (normal text),
            - :class:`discord.Embed`,
            - :ref:`FILE`,
            - List/Tuple containing any of the above arguments (There can up to 1 string, up to 1 :class:`discord.Embed` and up to 10 :ref:`FILE` objects. If more than 1 string or embeds are sent, the framework will only consider the last found).
            - Function that accepts any amount of parameters and returns any of the above types. To pass a function, YOU MUST USE THE :ref:`data_function` decorator on the function before passing the function to the daf.

    mode: Optional[str]
        Parameter that defines how message will be sent to a channel.
        It can be:

        - "send" -    each period a new message will be sent,
        - "edit" -    each period the previously send message will be edited (if it exists)
        - "clear-send" -    previous message will be deleted and a new one sent.

    start_in: Optional[timedelta]
        When should the message be first sent.
    remove_after: Optional[Union[int, timedelta, datetime]]
        Deletes the guild after:

        * int - provided amounts of sends
        * timedelta - the specified time difference
        * datetime - specific date & time
    """

    __slots__ = (
        "mode",
        "previous_message",
        "dm_channel",
    )

    @typechecked
    def __init__(self,
                 start_period: Union[int, timedelta, None],
                 end_period: Union[int, timedelta],
                 data: TMDataType,
                 mode: Optional[Literal["send", "edit", "clear-send"]] = "send",
                 start_in: Optional[Union[timedelta, bool]] = timedelta(seconds=0),
                 remove_after: Optional[Union[int, timedelta, datetime]]=None):
        super().__init__(start_period, end_period, data, start_in, remove_after)
        self.mode = mode
        self.dm_channel = None
        self.previous_message = None
    
    def generate_log_context(self,
                              success_context: Dict[str, Union[bool, Optional[Exception]]],
                              text : Optional[str],
                              embed : Optional[Union[discord.Embed, EMBED]],
                              files : List[FILE]) -> Dict[str, Any]:
        """
        Generates information about the message send attempt that is to be saved into a log.

        Parameters
        -----------
        text: str
            The text that was sent.
        embed: discord.Embed
            The embed that was sent.
        files: List[FILE]
            List of files that were sent.
        success_context: Dict[bool, Exception]
            Dictionary containing information about succession of the DM attempt.
            Contains "success": `bool` key and "reason": `Exception` key which is only present if "success" is `False`


        Returns
        ----------
        Dict[str, Any]
            .. code-block:: python

                {
                    sent_data:
                    {
                        text: str - The text that was sent,
                        embed: Dict[str, Any] - The embed that was sent,
                        files: List[str] - List of files that were sent.
                    },
                    success_info:
                    {
                        success: bool - Was sending successful or not,
                        reason:  str  - If it was unsuccessful, what was the reason
                    },
                    type: str - The type of the message, this is always DirectMESSAGE,
                    mode: str - The mode used to send the message (send, edit, clear-send)
                }
        """
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

    async def _get_data(self) -> dict:
        """
        Returns a dictionary of keyword arguments that is then expanded
        into other functions (_send_channel, _generate_log).
        This is exactly the same as in :ref:`TextMESSAGE`.

        .. versionchanged:: v2.3
            Turned async.
        """
        data = await super()._get_data()
        _data_to_send = {"embed": None, "text": None, "files": []}
        if data is not None:
            if not isinstance(data, (list, tuple, set)):
                data = (data,)
            for element in data:
                if isinstance(element, str):
                    _data_to_send["text"] = element
                elif isinstance(element, (EMBED, discord.Embed)):
                    _data_to_send["embed"] = element
                elif isinstance(element, FILE):
                    _data_to_send["files"].append(element)
        return _data_to_send

    async def initialize(self, parent: Any):
        """
        The method creates a direct message channel and
        returns True on success or False on failure

        .. versionchanged:: v2.1
            Renamed user to and changed the type from discord.User to daf.guild.USER

        Parameters
        -----------
        parent: daf.guild.USER
            The USER this message is in

        Raises
        ---------
        ValueError
            Raised when the direct message channel could not be created
        """
        try:
            self.parent = parent
            user = parent.apiobject
            await user.create_dm()
            self.dm_channel = user
        except discord.HTTPException as ex:
            raise ValueError(f"Unable to create DM with user {user.display_name}\nReason: {ex}")

    async def _handle_error(self, ex: Exception) -> bool:
        """
        This method handles the error that occurred during the execution of the function.
        Returns `True` if error was handled.

        Parameters
        -----------
        ex: Exception
            The exception that occurred during a send attempt.
        """
        handled = False
        if isinstance(ex, discord.HTTPException):
            if ex.status == 429 or ex.code == 40003: # Too Many Requests or opening DMs too fast
                retry_after = int(ex.response.headers["Retry-After"]) + 1
                await asyncio.sleep(retry_after)
                handled = True
            elif ex.status == 404:      # Unknown object
                if ex.code == 10008:    # Unknown message
                    self.previous_message = None
                    handled = True

        return handled

    async def _send_channel(self,
                           text: Optional[str],
                           embed: Optional[Union[discord.Embed, EMBED]],
                           files: List[FILE]) -> dict:
        """
        Sends data to the DM channel (user).

        Returns
        ------------
        Returns a dictionary:
        - "success" - Returns True if successful, else False.
        - "reason"  - Only present if "success" is False, contains the Exception returned by the send attempt.
        """
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
                if await self._handle_error(ex) is False or tries == 2:
                    return {"success" : False, "reason" : ex}

    @misc._async_safe("update_semaphore")
    async def _send(self) -> Union[dict, None]:
        """
        Sends the data into the channels

        Returns
        ----------
        Tuple[Union[dict, None], bool]
            Returns a tuple of logging context and bool
            variable that signals the upper layer all other messages should be removed
            due to a forbidden error which automatically causes other messages to fail
            and increases risk of getting a user account banned.
        """
        # Parse data from the data parameter
        data_to_send = await self._get_data()
        context, panic = None, False
        if any(data_to_send.values()):            
            context = await self._send_channel(**data_to_send)
            self._update_state()
            panic = ("reason" in context and context["reason"].status in {400, 403})
            context = self.generate_log_context(context, **data_to_send)

        return context, panic

    @typechecked
    @misc._async_safe("update_semaphore")
    async def update(self, _init_options: Optional[dict] = {}, **kwargs):
        """
        .. versionadded:: v2.0

        Used for changing the initialization parameters the object was initialized with.

        .. warning::
            Upon updating, the internal state of objects get's reset, meaning you basically have a brand new created object.

        Parameters
        -------------
        kwargs: Any
            Custom number of keyword parameters which you want to update, these can be anything that is available during the object creation.

        Raises
        -----------
        TypeError
            Invalid keyword argument was passed
        Other
            Raised from .initialize() method
        """

        if "start_in" not in kwargs:
            # This parameter does not appear as attribute, manual setting necessary
            kwargs["start_in"] = timedelta(seconds=0)

        if "data" not in kwargs:
            kwargs["data"] = self._data

        if not len(_init_options):
            _init_options = {"parent" : self.parent}

        await misc._update(self, init_options=_init_options, **kwargs) # No additional modifications are required
