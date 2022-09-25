"""
Contains definitions for message classes that are text based."""


from pickle import GLOBAL
from typing import Any, Dict, List, Iterable, Optional, Union, Literal
from datetime import datetime, timedelta
from typeguard import typechecked

from .base import *
from ..dtypes import *
from ..tracing import *
from ..common import *
from ..exceptions import *

from .. import client
from .. import sql
from .. import misc

import asyncio
import _discord as discord


__all__ = (
    "TextMESSAGE",
    "DirectMESSAGE"
)

@typechecked
@sql._register_type("MessageTYPE")
class TextMESSAGE(BaseMESSAGE):
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
            daf.TextMESSAGE(start_period=timedelta(5), end_period=timedelta(10), data="Second Message", channels=[12345], mode="send", start_in=timedelta(seconds=0))

        .. code-block:: python
            :caption: **Fixed** sending period at **10** seconds

            # Time between each send is exactly 10 seconds.
            daf.TextMESSAGE(start_period=None, end_period=timedelta(10), data="Second Message", channels=[12345], mode="send", start_in=timedelta(seconds=0))

    data: Union[str, EMBED, FILE, List[Union[str, EMBED, FILE]], _FunctionBaseCLASS]
        The data parameter is the actual data that will be sent using discord's API. The data types of this parameter can be:
            - str (normal text),
            - :ref:`EMBED`,
            - :ref:`FILE`,
            - List/Tuple containing any of the above arguments (There can up to 1 string, up to 1 :ref:`EMBED` and up to 10 :ref:`FILE` objects. If more than 1 string or embeds are sent, the framework will only consider the last found).
            - Function that accepts any amount of parameters and returns any of the above types. To pass a function, YOU MUST USE THE :ref:`data_function` decorator on the function before passing the function to the daf.

    channels: Iterable[Union[int, discord.TextChannel, discord.Thread]]
        Channels that it will be advertised into (Can be snowflake ID or channel objects from PyCord).
    mode: str
        Parameter that defines how message will be sent to a channel.
        It can be:

        - "send" -    each period a new message will be sent,
        - "edit" -    each period the previously send message will be edited (if it exists)
        - "clear-send" -    previous message will be deleted and a new one sent.

    start_in: timedelta
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
    __logname__: str = "TextMESSAGE"               # Used for registering SQL types and to get the message type for saving the log

    def __init__(self, 
                 start_period: Union[int, timedelta, None],
                 end_period: Union[int, timedelta],
                 data: Union[str, EMBED, FILE, Iterable[Union[str, EMBED, FILE]], _FunctionBaseCLASS],
                 channels: Iterable[Union[int, discord.TextChannel, discord.Thread]],
                 mode: Literal["send", "edit", "clear-send"] = "send",
                 start_in: Union[timedelta, bool]=timedelta(seconds=0),
                 remove_after: Optional[Union[int, timedelta, datetime]]=None):
        super().__init__(start_period, end_period, data, start_in, remove_after)
        self.mode = mode
        self.channels = list(set(channels)) # Automatically removes duplicates
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

    def _generate_log_context(self,
                             text: Optional[str],
                             embed: Optional[EMBED],
                             files: List[FILE],
                             succeeded_ch: List[Union[discord.TextChannel, discord.Thread]],
                             failed_ch: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generates information about the message send attempt that is to be saved into a log.

        Parameters
        -----------
        text: str
            The text that was sent.
        embed: EMBED
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
            Dictionary containing:

                - sent_data: Dict[str, Any]:
                    - text: str
                        The text that was sent.
                    - embed: Dict[str, Any]
                        The embed that was sent.
                    - files: List[str]
                        List of files that were sent.

                - channels: Dict[str, List]:
                    - successful: List[Dict[str, int]] - List of dictionaries containing name of the channel and snowflake id of the channels.
                    - failed: List[Dict[str, Any]] - List of dictionaries containing name of the channel (str), snowflake id (int) and reason why streaming to channel failed (str).

                - type: str - The type of the message, this is always TextMESSAGE.
                - mode: str - The mode used to send the message (send, edit, clear-send).
        """

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

    def _get_data(self) -> dict:
        """"
        Returns a dictionary of keyword arguments that is then expanded
        into other methods eg. `_send_channel, _generate_log`
        """
        data = self.data.get_data() if isinstance(self.data, _FunctionBaseCLASS) else self.data
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
        cl = client.get_client()
        self.parent = parent
        _guild = self.parent.apiobject
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
                raise TypeError(f"TextMESSAGE object received channel type of {type(channel).__name__}, but was expecting discord.TextChannel or discord.Thread")
            elif channel.guild != _guild:
                raise ValueError(f"The channel {channel.name}(ID: {channel_id}) does not belong into {_guild.name}(ID: {_guild.id}) but is part of {channel.guild.name}(ID: {channel.guild.id})")
            else:
                ch_i += 1

        if not len(self.channels):
            raise ValueError(f"No valid channels were passed to {self} object")

    async def _handle_error(self, channel: Union[discord.TextChannel, discord.Thread], ex: Exception) -> bool:
        """
        This method handles the error that occurred during the execution of the function.
        Returns `True` if error was handled.

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
            elif ex.status == 404:      # Unknown object
                if ex.code == 10008:    # Unknown message
                    self.sent_messages[channel.id] = None
                    handled = True

        return handled

    async def _send_channel(self,
                           channel: Union[discord.TextChannel, discord.Thread, None],
                           text: Optional[str],
                           embed: Optional[EMBED],
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
        embed: EMBED
            The embedded frame to send.
        files: List[FILE]
            List of files to send.
        """

        ch_perms = channel.permissions_for(channel.guild.get_member(client.get_client().user.id))
        for tries in range(3):  # Maximum 3 tries (if rate limit)
            try:
                # Check if we have permissions
                if ch_perms.send_messages is False:
                    raise self._generate_exception(403, 50013, "You lack permissions to perform that action", discord.Forbidden)

                # Check if channel still exists in cache (has not been deleted)
                if client.get_client().get_channel(channel.id) is None:
                    raise self._generate_exception(404, 10003, "Channel was deleted", discord.NotFound)

                # Delete previous message if clear-send mode is chosen and message exists
                if self.mode == "clear-send" and self.sent_messages.get(channel.id, None) is not None:
                    await self.sent_messages[channel.id].delete()
                    self.sent_messages[channel.id] = None

                # Send/Edit message
                if (self.mode in {"send" , "clear-send"} or # Mode dictates to send new message or delete previous and then send new message or mode dictates edit but message was  never sent to this channel before
                    self.mode == "edit" and self.sent_messages.get(channel.id, None) is None
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
                if not await self._handle_error(channel, ex):
                    return {"success" : False, "reason" : ex}

    @misc._async_safe("update_semaphore")
    async def _send(self) -> Union[dict, None]:
        """
        Sends the data into the channels.

        Returns
        ----------
        Union[Dict, None]
            Returns a dictionary generated by the ``_generate_log_context`` method or the None object if message wasn't ready to be sent (:ref:`data_function` returned None or an invalid type)

            This is then passed to :ref:`GUILD`._generate_log method.
        """
        # Acquire mutex to prevent update method from writing while sending
        data_to_send = self._get_data()
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
            return self._generate_log_context(**data_to_send, succeeded_ch=succeeded_channels, failed_ch=errored_channels) # Return sent data + failed and successful function for logging purposes

        return None

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
        
        if not len(_init_options):
            _init_options = {"guild": self.parent.apiobject}

        await misc._update(self, init_options=_init_options, **kwargs) # No additional modifications are required


@typechecked
@sql._register_type("MessageTYPE")
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
            daf.DirectMESSAGE(start_period=timedelta(5), end_period=timedelta(10), data="Second Message",  mode="send", start_in=timedelta(seconds=0))

        .. code-block:: python
            :caption: **Fixed** sending period at **10** seconds

            # Time between each send is exactly 10 seconds.
            daf.DirectMESSAGE(start_period=None, end_period=timedelta(10), data="Second Message",  mode="send", start_in=timedelta(seconds=0))

    data: Union[str, EMBED, FILE, List[Union[str, EMBED, FILE]], _FunctionBaseCLASS]
        The data parameter is the actual data that will be sent using discord's API. The data types of this parameter can be:
            - str (normal text),
            - :ref:`EMBED`,
            - :ref:`FILE`,
            - List/Tuple containing any of the above arguments (There can up to 1 string, up to 1 :ref:`EMBED` and up to 10 :ref:`FILE` objects. If more than 1 string or embeds are sent, the framework will only consider the last found).
            - Function that accepts any amount of parameters and returns any of the above types. To pass a function, YOU MUST USE THE :ref:`data_function` decorator on the function before passing the function to the daf.

    mode: str
        Parameter that defines how message will be sent to a channel.
        It can be:

        - "send" -    each period a new message will be sent,
        - "edit" -    each period the previously send message will be edited (if it exists)
        - "clear-send" -    previous message will be deleted and a new one sent.

    start_in: timedelta
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
    __logname__ = "DirectMESSAGE"               # Used for logging (type key) and sql lookup table type registration

    def __init__(self,
                 start_period: Union[int, timedelta, None],
                 end_period: Union[int, timedelta],
                 data: Union[str, EMBED, FILE, Iterable[Union[str, EMBED, FILE]], _FunctionBaseCLASS],
                 mode: Literal["send", "edit", "clear-send"] = "send",
                 start_in: Union[timedelta, bool] = timedelta(seconds=0),
                 remove_after: Optional[Union[int, timedelta, datetime]]=None):
        super().__init__(start_period, end_period, data, start_in, remove_after)
        self.mode = mode
        self.dm_channel = None
        self.previous_message = None
    
    def _generate_log_context(self,
                              success_context: Dict[str, Union[bool, Optional[Exception]]],
                              text : Optional[str],
                              embed : Optional[EMBED],
                              files : List[FILE]) -> Dict[str, Any]:
        """
        Generates information about the message send attempt that is to be saved into a log.

        Parameters
        -----------
        text: str
            The text that was sent.
        embed: EMBED
            The embed that was sent.
        files: List[FILE]
            List of files that were sent.
        success_context: Dict[bool, Exception]
            Dictionary containing information about succession of the DM attempt.
            Contains "success": `bool` key and "reason": `Exception` key which is only present if "success" is `False`


        Returns
        ----------
        Dict[str, Any]
            Dictionary containing:

                - sent_data: Dict[str, str]:
                    - streamed_audio - The filename that was streamed/youtube url

                - success_info: Dict[str, Any]:
                    - success: bool - Was sending successful or not
                    - reason:  str  - If it was unsuccessful, what was the reason
                    - delete: bool  - Signals the guild object to remove this message from the list
                                      due to unrecoverable error (if set to True).

                - type: str - The type of the message, this is always TextMESSAGE.
                - mode: str - The mode used to send the message (send, edit, clear-send).
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

    def _get_data(self) -> dict:
        """
        Returns a dictionary of keyword arguments that is then expanded
        into other functions (_send_channel, _generate_log).
        This is exactly the same as in :ref:`TextMESSAGE`
        """
        return TextMESSAGE._get_data(self)

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
        DAFNotFoundError(code=DAF_USER_CREATE_DM)
            Raised when the direct message channel could not be created
        """
        try:
            user = parent.apiobject
            await user.create_dm()
            self.dm_channel = user
            self.parent = parent
        except discord.HTTPException as ex:
            raise DAFNotFoundError(f"Unable to create DM with user {user.display_name}\nReason: {ex}", DAF_USER_CREATE_DM)

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
                trace(f"Rate limited, sleeping for {retry_after} seconds", TraceLEVELS.WARNING)
                await asyncio.sleep(retry_after)
                handled = True
            elif ex.status == 404:      # Unknown object
                if ex.code == 10008:    # Unknown message
                    self.previous_message = None
                    handled = True
            elif ex.status == 403 or ex.code in {50007, 10001, 10003}:
                # Not permitted to send messages to that user!
                # Remove all messages to prevent an account ban
                for m in self.parent.messages:
                    if m in self.parent.messages:
                        self.parent.remove_message(m)

            if ex.status in {400, 403}: # Bad Request
                await asyncio.sleep(RLIM_USER_WAIT_TIME * 5) # To avoid triggering self-bot detection

        return handled

    async def _send_channel(self,
                           text: Optional[str],
                           embed: Optional[EMBED],
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
        Union[Dict, None]
            Returns a dictionary generated by the ``_generate_log_context`` method or the None object if message wasn't ready to be sent (:ref:`data_function` returned None or an invalid type)

            This is then passed to :ref:`GUILD`._generate_log method.
        """
        # Parse data from the data parameter
        data_to_send = self._get_data()
        if any(data_to_send.values()):            
            context = await self._send_channel(**data_to_send)
            self._update_state()
            return self._generate_log_context(context, **data_to_send)

        return None

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

        if not len(_init_options):
            _init_options = {"user" : self.parent.apiobject}

        await misc._update(self, init_options=_init_options, **kwargs) # No additional modifications are required
