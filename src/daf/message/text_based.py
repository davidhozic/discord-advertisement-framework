"""
Contains definitions for message classes that are text based."""

from typing import Any, Dict, List, Iterable, Optional, Union, Literal, Tuple, Callable
from datetime import datetime, timedelta
from typeguard import typechecked

from .base import *
from ..dtypes import *
from ..logging.tracing import trace, TraceLEVELS

from ..logging import sql
from ..misc import doc, instance_track, async_util
from ..events import *

import asyncio
import _discord as discord


__all__ = (
    "TextMESSAGE",
    "DirectMESSAGE"
)


# Register message modes
sql.register_type("MessageMODE", "send")
sql.register_type("MessageMODE", "edit")
sql.register_type("MessageMODE", "clear-send")


@instance_track.track_id
@doc.doc_category("Messages", path="message")
@sql.register_type("MessageTYPE")
class TextMESSAGE(BaseChannelMessage):
    """
    This class is used for creating objects that represent messages which will be sent to Discord's TEXT CHANNELS.

    Parameters
    ------------
    start_period: Union[int, timedelta, None]
        The value of this parameter can be:

        - None - Use this value for a fixed (not randomized) sending period
        - timedelta object - object describing time difference,
          if this is used, then the parameter represents the bottom limit of the **randomized** sending period.
    end_period: Union[int, timedelta]
        If ``start_period`` is not None,
        then this represents the upper limit of randomized time period in which messages will be sent.
        If ``start_period`` is None, then this represents the actual time period between each message send.

        .. CAUTION::
            When the period is lower than the remaining time, the framework will start
            incrementing the original period by original period until it is larger then
            the slow mode remaining time.

        .. code-block:: python
            :caption: **Randomized** sending period between **5** seconds and **10** seconds.

            # Time between each send is somewhere between 5 seconds and 10 seconds.
            daf.TextMESSAGE(start_period=timedelta(seconds=5), end_period=timedelta(seconds=10), data="Second Message",
                            channels=[12345], mode="send", start_in=timedelta(seconds=0))

        .. code-block:: python
            :caption: **Fixed** sending period at **10** seconds

            # Time between each send is exactly 10 seconds.
            daf.TextMESSAGE(start_period=None, end_period=timedelta(seconds=10), data="Second Message",
                            channels=[12345], mode="send", start_in=timedelta(seconds=0))
    data: Union[str, discord.Embed, FILE, List[Union[str, discord.Embed, FILE]], _FunctionBaseCLASS]
        The data parameter is the actual data that will be sent using discord's API.
        The data types of this parameter can be:

            - str (normal text),
            - :class:`discord.Embed`,
            - :ref:`FILE`,
            - List/Tuple containing any of the above arguments (There can up to 1 string, up to 1 :class:`discord.Embed` and up to 10 :ref:`FILE` objects.
            - Function that accepts any amount of parameters and returns any of the above types. To pass a function, YOU MUST USE THE :ref:`data_function` decorator on the function before passing the function to the daf.

    channels: Union[Iterable[Union[int, discord.TextChannel, discord.Thread]], daf.message.AutoCHANNEL]
        Channels that it will be advertised into (Can be snowflake ID or channel objects from PyCord).

        .. versionchanged:: v2.3
            Can also be :class:`~daf.message.AutoCHANNEL`

        .. note::

            If no channels are left, the message is automatically removed, unless AutoCHANNEL is used.

    mode: Optional[str]
        Parameter that defines how message will be sent to a channel.
        It can be:

        - "send" -    each period a new message will be sent,
        - "edit" -    each period the previously send message will be edited (if it exists)
        - "clear-send" -    previous message will be deleted and a new one sent.
    start_in: Optional[timedelta | datetime]
        When should the message be first sent.
        *timedelta* means the difference from current time, while *datetime* means actual first send time.
    remove_after: Optional[Union[int, timedelta, datetime]]
        Deletes the message after:

        * int - provided amounts of successful sends to seperate channels.
        * timedelta - the specified time difference
        * datetime - specific date & time

        .. versionchanged:: 2.10

            Parameter ``remove_after`` of int type will now work at a channel level and
            it nows means the SUCCESSFUL number of sends into each channel.

    auto_publish: Optional[bool]
        Automatically publish message if sending to an announcement channel.
        Defaults to False.

        If the channel publish is rate limited, the message will still be sent, but an error will be
        printed to the console instead of message being published to the follower channels.

        .. versionadded:: 2.10
    """

    __slots__ = (
        "mode",
        "sent_messages",
        "auto_publish",
    )

    @typechecked
    def __init__(
        self,
        start_period: Union[timedelta, int, None],
        end_period: Union[int, timedelta],
        data: Union[Iterable[Union[str, discord.Embed, FILE]], str, discord.Embed, FILE, _FunctionBaseCLASS],
        channels: Union[Iterable[Union[int, discord.TextChannel, discord.Thread]], AutoCHANNEL],
        mode: Literal["send", "edit", "clear-send"] = "send",
        start_in: Union[timedelta, datetime] = timedelta(seconds=0),
        remove_after: Optional[Union[int, timedelta, datetime]] = None,
        auto_publish: bool = False
    ):
        super().__init__(start_period, end_period, data, channels, start_in, remove_after)
        self.mode = mode
        self.auto_publish = auto_publish
        # Dictionary for storing last sent message for each channel
        self.sent_messages: Dict[int, discord.Message] = {}

    @property
    def _slowmode(self) -> timedelta:
        """
        The maximum slowmode delay of the message's channels.

        Returns
        ----------
        timedelta
            The maximum slowmode delay of all channels.
        """
        seconds = max((c.slowmode_delay for c in self.channels), default=0)
        if seconds > 0:  # To be sure
            seconds += 10

        return timedelta(seconds=seconds)

    def _check_period(self):
        """
        Helper function used for checking the the period is lower
        than the slow mode delay.

        .. versionadded:: v2.3

        Parameters
        --------------
        slowmode_delay: timedelta
            The (maximum) slowmode delay.
        """
        slowmode_delay = self._slowmode
        if self.start_period is not None:
            if self.start_period < slowmode_delay:
                self.start_period, self.end_period = (
                    slowmode_delay,
                    slowmode_delay + self.end_period - self.start_period
                )
        elif self.end_period < slowmode_delay:
            self.end_period = slowmode_delay

        self.period = self.end_period

    def generate_log_context(self,
                             text: Optional[str],
                             embed: discord.Embed,
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

        succeeded_ch = [{"name": str(channel), "id": channel.id} for channel in succeeded_ch]
        failed_ch = [{"name": str(entry["channel"]), "id": entry["channel"].id,
                     "reason": str(entry["reason"])} for entry in failed_ch]

        embed = embed.to_dict() if embed is not None else None

        files = [x.fullpath for x in files]
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
                "successful": succeeded_ch,
                "failed": failed_ch
            },
            "type": type(self).__name__,
            "mode": self.mode,
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
                elif isinstance(element, discord.Embed):
                    _data_to_send["embed"] = element
                elif isinstance(element, FILE):
                    _data_to_send["files"].append(element)
        return _data_to_send

    def _get_channel_types(self):
        return {discord.TextChannel, discord.Thread}

    async def initialize(self, parent: Any, event_ctrl: EventController, channel_getter: Callable):
        """
        This method initializes the implementation specific API objects and
        checks for the correct channel input context.

        Parameters
        --------------
        parent: daf.guild.GUILD
            The GUILD this message is in
        """
        exc = await super().initialize(
            parent,
            event_ctrl,
            channel_getter
        )
        if exc is not None:
            return exc

        # Increase period to slow mode delay if it is lower
        self._check_period()

    async def _handle_error(
        self,
        channel: Union[discord.TextChannel, discord.Thread],
        ex: Exception
    ) -> Tuple[bool, ChannelErrorAction]:
        """
        This method handles the error that occurred during the execution of the function.

        Parameters
        -----------
        channel: Union[discord.TextChannel, discord.Thread]
            The channel where the exception occurred.
        ex: Exception
            The exception that occurred during a send attempt.

        Returns
        -----------
        Tuple[bool, ChannelErrorAction]
            Tuple containing (error_handled, ChannelErrorAction),
            where the ChannelErrorAction is a enum telling upper part of the message layer how to proceed.
        """
        handled = False
        action = None

        if isinstance(ex, discord.HTTPException):
            if ex.status == 403:
                # Timeout handling
                guild = channel.guild
                member = guild.get_member(self.parent.parent.client.user.id)
                if member is not None and member.timed_out:
                    self.next_send_time = member.communication_disabled_until.astimezone() + timedelta(minutes=1)
                    trace(
                        f"User '{member.name}' has been timed-out in guild '{guild.name}'.\n"
                        f"Retrying after {self.next_send_time} (1 minute after expiry)",
                        TraceLEVELS.WARNING
                    )
                    # Prevent channel removal by the cleanup process
                    ex.status = 429
                    ex.code = 0
                    action = ChannelErrorAction.SKIP_CHANNELS  # Don't try to send to other channels as it would yield the same result.

            elif ex.status == 429:  # Rate limit
                retry_after = int(ex.response.headers["Retry-After"]) + 5
                if ex.code == 20016:    # Slow Mode
                    self.next_send_time = datetime.now().astimezone() + timedelta(seconds=retry_after)
                    trace(f"{channel.name} is in slow mode, retrying in {retry_after} seconds", TraceLEVELS.WARNING)
                    self._check_period()  # Fix the period

            elif ex.status == 404:      # Unknown object
                if ex.code == 10008:    # Unknown message
                    self.sent_messages[channel.id] = None
                    handled = True

            elif ex.status == 401:  # Token invalidated
                action = ChannelErrorAction.REMOVE_ACCOUNT

        return handled, action

    async def _send_channel(self,
                            channel: Union[discord.TextChannel, discord.Thread, None],
                            text: Optional[str],
                            embed: Optional[discord.Embed],
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
                member = channel.guild.get_member(client_.user.id)
                if member is None:
                    raise self._generate_exception(
                        404, -1, "Client user could not be found in guild members", discord.NotFound
                    )

                if channel.guild.me.pending:
                    raise self._generate_exception(
                        403, 50009,
                        "Channel verification level is too high for you to gain access",
                        discord.Forbidden
                    )

                ch_perms = channel.permissions_for(member)
                if ch_perms.send_messages is False:
                    raise self._generate_exception(
                        403, 50013, "You lack permissions to perform that action", discord.Forbidden
                    )

                # Check if channel still exists in cache (has not been deleted)
                if client_.get_channel(channel.id) is None:
                    raise self._generate_exception(404, 10003, "Channel was deleted", discord.NotFound)

                # Delete previous message if clear-send mode is chosen and message exists
                if self.mode == "clear-send" and self.sent_messages.get(channel.id, None) is not None:
                    await self.sent_messages[channel.id].delete()
                    self.sent_messages[channel.id] = None

                # Send/Edit message
                if (
                    self.mode in {"send", "clear-send"} or
                    self.mode == "edit" and self.sent_messages.get(channel.id, None) is None
                ):
                    message = await channel.send(
                        text,
                        embed=embed,
                        files=[discord.File(file.stream, file.filename) for file in files]
                    )
                    self.sent_messages[channel.id] = message
                    await self._publish_message(message)

                # Mode is edit and message was already send to this channel
                elif self.mode == "edit":
                    await self.sent_messages[channel.id].edit(text, embed=embed)

                return {"success": True}

            except Exception as ex:
                handled, action = await self._handle_error(channel, ex)
                if not handled:
                    return {"success": False, "reason": ex, "action": action}

    async def _publish_message(self, message: discord.Message):
        channel = message.channel
        if self.auto_publish and channel.is_news():
            try:
                await message.publish()
            except discord.HTTPException as exc:
                trace(
                    f"Unable to publish {self} to channel '{channel.name}'({channel.id})",
                    TraceLEVELS.ERROR,
                    exc
                )


@instance_track.track_id
@doc.doc_category("Messages", path="message")
@sql.register_type("MessageTYPE")
class DirectMESSAGE(BaseMESSAGE):
    """
    This class is used for creating objects that represent messages which will be sent to user's private messages.

    .. deprecated:: v2.1

        - start_period, end_period - Using int values, use ``timedelta`` object instead.

    .. versionchanged:: v2.7

        *start_in* now accepts datetime object

    Parameters
    ------------
    start_period: Union[int, timedelta, None]
        The value of this parameter can be:

        - None - Use this value for a fixed (not randomized) sending period
        - timedelta object - object describing time difference, if this is used,
          then the parameter represents the bottom limit of the **randomized** sending period.

    end_period: Union[int, timedelta]
        If ``start_period`` is not None, then this represents the upper limit of randomized time period
        in which messages will be sent.
        If ``start_period`` is None, then this represents the actual time period between each message send.

        .. code-block:: python
            :caption: **Randomized** sending period between **5** seconds and **10** seconds.

            # Time between each send is somewhere between 5 seconds and 10 seconds.
            daf.DirectMESSAGE(
                start_period=timedelta(seconds=5), end_period=timedelta(seconds=10), data="Second Message",
                mode="send", start_in=timedelta(seconds=0)
            )

        .. code-block:: python
            :caption: **Fixed** sending period at **10** seconds

            # Time between each send is exactly 10 seconds.
            daf.DirectMESSAGE(
                start_period=None, end_period=timedelta(seconds=10), data="Second Message",
                mode="send", start_in=timedelta(seconds=0)
            )

    data: Union[str, discord.Embed FILE, List[Union[str, discord.Embed, FILE]], _FunctionBaseCLASS]
        The data parameter is the actual data that will be sent using discord's API.
        The data types of this parameter can be:

        - str (normal text),
        - :class:`discord.Embed`,
        - :ref:`FILE`,
        - List/Tuple containing any of the above arguments
          (There can up to 1 string, up to 1 :class:`discord.Embed` and up to 10 :ref:`FILE` objects.
        - Function that accepts any amount of parameters and returns any of the above types.
          To pass a function, YOU MUST USE THE :ref:`data_function` decorator on the function.

    mode: Optional[str]
        Parameter that defines how message will be sent to a channel.
        It can be:

        - "send" -    each period a new message will be sent,
        - "edit" -    each period the previously send message will be edited (if it exists)
        - "clear-send" -    previous message will be deleted and a new one sent.

    start_in: Optional[timedelta | datetime]
        When should the message be first sent.
        *timedelta* means the difference from current time, while *datetime* means actual first send time.
    remove_after: Optional[Union[int, timedelta, datetime]]
        Deletes the guild after:

        * int - provided amounts of successful sends
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
                 data: Union[str, discord.Embed, FILE, Iterable[Union[str, discord.Embed, FILE]], _FunctionBaseCLASS],
                 mode: Optional[Literal["send", "edit", "clear-send"]] = "send",
                 start_in: Optional[Union[timedelta, datetime]] = timedelta(seconds=0),
                 remove_after: Optional[Union[int, timedelta, datetime]] = None):
        super().__init__(start_period, end_period, data, start_in, remove_after)
        self.mode = mode
        self.dm_channel: discord.User = None
        self.previous_message: discord.Message = None

    def _update_state(self) -> bool:
        """
        Updates internal remove_after counter.
        """
        if type(self._remove_after) is int:
            self._remove_after -= 1
            if not self._remove_after:
                self._event_ctrl.emit(EventID.message_removed, self.parent, self)


    def generate_log_context(self,
                             success_context: Dict[str, Union[bool, Optional[Exception]]],
                             text: Optional[str],
                             embed: Optional[discord.Embed],
                             files: List[FILE]) -> Dict[str, Any]:
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
        files = [x.fullpath for x in files]

        success_context = success_context.copy()  # Don't modify outside
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
            "type": type(self).__name__,
            "mode": self.mode
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
                elif isinstance(element, discord.Embed):
                    _data_to_send["embed"] = element
                elif isinstance(element, FILE):
                    _data_to_send["files"].append(element)
        return _data_to_send

    @async_util.except_return
    async def initialize(self, parent: Any, event_ctrl: EventController, guild: discord.User):
        """
        The method creates a direct message channel and
        returns True on success or False on failure

        .. versionchanged:: v2.1
            Renamed user to and changed the type from discord.User to daf.guild.USER

        Parameters
        -----------
        parent: daf.guild.USER
            The USER this message is in
        """
        try:
            self.parent = parent
            await guild.create_dm()
            self.dm_channel = guild
            return await super().initialize(event_ctrl)
        except discord.HTTPException as exc:
            trace(f"Unable to create DM with user {guild.display_name}", TraceLEVELS.ERROR, exc)
            raise

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
            if ex.status == 429 or ex.code == 40003:  # Too Many Requests or opening DMs too fast
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
                            embed: Optional[discord.Embed],
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
                if (
                    self.mode in {"send", "clear-send"} or
                    self.mode == "edit" and self.previous_message is None
                ):
                    self.previous_message = await self.dm_channel.send(
                        text,
                        embed=embed,
                        files=[discord.File(fwFILE.stream, fwFILE.filename) for fwFILE in files]
                    )

                # Mode is edit and message was already send to this channel
                elif self.mode == "edit":
                    await self.previous_message.edit(text, embed=embed)

                return {"success": True}

            except Exception as ex:
                if await self._handle_error(ex) is False or tries == 2:
                    return {"success": False, "reason": ex}

    @async_util.with_semaphore("update_semaphore")
    async def _send(self) -> Union[dict, None]:
        """
        Sends the data into the channels
        """
        # Parse data from the data parameter
        data_to_send = await self._get_data()
        if any(data_to_send.values()):
            channel_ctx = await self._send_channel(**data_to_send)
            self._update_state()
            if channel_ctx["success"] is False:
                reason = channel_ctx["reason"]
                if isinstance(reason, discord.HTTPException):
                    if reason.status in {400, 403}:  # Bad request, forbidden
                        self._event_ctrl.emit(EventID.server_removed, self.parent)
                    elif reason.status == 401:  # Unauthorized (invalid token)
                        self._event_ctrl.emit(EventID.g_account_expired, self.parent.parent)

            return self.generate_log_context(channel_ctx, **data_to_send)

        return None

    def update(self, _init_options: Optional[dict] = None, **kwargs) -> asyncio.Future:
        return self._event_ctrl.emit(EventID.message_update, self, _init_options, **kwargs)

    async def _on_update(self, _, _init_options: Optional[dict], **kwargs):
        await self._close()
        if "start_in" not in kwargs:
            # This parameter does not appear as attribute, manual setting necessary
            kwargs["start_in"] = self.next_send_time

        if "data" not in kwargs:
            kwargs["data"] = self._data

        if _init_options is None:
            _init_options = {"parent": self.parent, "guild": self.dm_channel, "event_ctrl": self._event_ctrl}

        try:
            await async_util.update_obj_param(self, init_options=_init_options, **kwargs)
        except Exception:
            await self.initialize(self.parent, self._event_ctrl, self.dm_channel)
            raise
