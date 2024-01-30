"""
Contains definitions for message classes that are text based."""

from typing import Any, Dict, List, Iterable, Optional, Union, Literal, Tuple, Callable
from datetime import datetime, timedelta
from typeguard import typechecked


from ..messagedata.dynamicdata import _DeprecatedDynamic

from ..messagedata import BaseTextData, TextMessageData, FILE
from ..logging.tracing import trace, TraceLEVELS
from .messageperiod import *
from .autochannel import *
from ..dtypes import *
from .base import *

from ..misc import doc, instance_track, async_util
from ..logging import sql
from ..events import *

import _discord as discord
import asyncio


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
    data: BaseTextData
        The data to be sent. Can be TextMessageData or class inherited from DynamicMessageData
    channels: Union[list[Union[int, discord.TextChannel, discord.Thread]], daf.message.AutoCHANNEL]
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

    _old_data_type = Union[list, tuple, set, str, discord.Embed, FILE, _FunctionBaseCLASS]

    @typechecked
    def __init__(
        self,
        start_period: Union[timedelta, int, None] = None,
        end_period: Union[int, timedelta] = None,
        data: Union[BaseTextData, _old_data_type] = None,
        channels: Union[list[Union[int, discord.TextChannel, discord.Thread]], AutoCHANNEL] = None,
        mode: Literal["send", "edit", "clear-send"] = "send",
        start_in: Optional[Union[timedelta, datetime]] = None,
        remove_after: Optional[Union[int, timedelta, datetime]] = None,
        auto_publish: bool = False,
        period: BaseMessagePeriod = None
    ):
        if not isinstance(data, BaseTextData):
            trace(
                f"Using data types other than {[x.__name__ for x in BaseTextData.__subclasses__()]}, "
                "is deprecated on TextMESSAGE's data parameter! Planned for removal in 4.2.0",
                TraceLEVELS.DEPRECATED
            )
            # Transform to new data type            
            if isinstance(data, _FunctionBaseCLASS):
                data = _DeprecatedDynamic(data.fnc, *data.args, **data.kwargs)
            elif data is not None:
                if isinstance(data, (str, discord.Embed, FILE)):
                    data = [data]

                content = None
                embed = None
                files = []
                for item in data:
                    if isinstance(item, str):
                        content = item
                    elif isinstance(item, discord.Embed):
                        embed = item
                    else:
                        files.append(item)

                data = TextMessageData(content, embed, files)

        super().__init__(start_period, end_period, data, channels, start_in, remove_after, period)
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
        .. versionchanged:: 4.0.0

            Changed to body to just call ``self.period.adjust``.

        Helper function used for checking the the period is lower
        than the slow mode delay.
        """
        self.period.adjust(self._slowmode)

    def generate_log_context(self,
                             content: Optional[str],
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
        if content is not None:
            sent_data_context["text"] = content
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
                    self.period.defer(member.communication_disabled_until.astimezone() + timedelta(minutes=1))
                    trace(
                        f"User '{member.name}' has been timed-out in guild '{guild.name}'.\n",
                        TraceLEVELS.WARNING
                    )
                    # Prevent channel removal by the cleanup process
                    ex.status = 429
                    ex.code = 0
                    action = ChannelErrorAction.SKIP_CHANNELS  # Don't try to send to other channels as it would yield the same result.

            elif ex.status == 429:  # Rate limit
                if ex.code == 20016:    # Slow Mode
                    self.period.defer(
                        datetime.now().astimezone() +
                        timedelta(seconds=int(ex.response.headers["Retry-After"]) + 5)
                    )
                    trace(f"{channel.name} is in slow mode. Retrying on {self.period.get()}", TraceLEVELS.WARNING)
                    self._check_period()  # Fix the period

            elif ex.status == 404:      # Unknown object
                if ex.code == 10008:    # Unknown message
                    self.sent_messages[channel.id] = None
                    handled = True

            elif ex.status == 401:  # Token invalidated
                action = ChannelErrorAction.REMOVE_ACCOUNT

        return handled, action

    def _verify_data(self, data: dict) -> bool:
        return super()._verify_data(TextMessageData, data)

    async def _send_channel(
        self,
        channel: Union[discord.TextChannel, discord.Thread, None],
        content: Optional[str],
        embed: Optional[discord.Embed],
        files: List[FILE]
    ) -> dict:
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
                        content,
                        embed=embed,
                        files=[discord.File(file.stream, file.filename) for file in files]
                    )
                    self.sent_messages[channel.id] = message
                    await self._publish_message(message)

                # Mode is edit and message was already send to this channel
                elif self.mode == "edit":
                    await self.sent_messages[channel.id].edit(content, embed=embed)

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
    data: BaseTextData
        The data to be sent. Can be TextMessageData or class inherited from DynamicMessageData
    mode: Optional[str]
        Parameter that defines how message will be sent to a channel.
        It can be:

        - "send" -    each period a new message will be sent,
        - "edit" -    each period the previously send message will be edited (if it exists)
        - "clear-send" -    previous message will be deleted and a new one sent.
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
    
    _old_data_type = Union[list, tuple, set, str, discord.Embed, FILE, _FunctionBaseCLASS]

    @typechecked
    def __init__(
        self,
        start_period: Union[int, timedelta, None] = None,
        end_period: Union[int, timedelta] = None,
        data: Union[BaseTextData, _old_data_type] = None,
        mode: Optional[Literal["send", "edit", "clear-send"]] = "send",
        start_in: Optional[Union[timedelta, datetime]] = None,
        remove_after: Optional[Union[int, timedelta, datetime]] = None,
        period: BaseMessagePeriod = None
    ):

        if not isinstance(data, BaseTextData):
            trace(
                f"Using data types other than {[x.__name__ for x in BaseTextData.__subclasses__()]}, "
                "is deprecated on DirectMESSAGE's data parameter! Planned for removal in 4.2.0",
                TraceLEVELS.DEPRECATED
            )
            # Transform to new data type            
            if isinstance(data, _FunctionBaseCLASS):
                data = _DeprecatedDynamic(data.fnc, *data.args, *data.kwargs)
            elif data is not None:
                if isinstance(data, (str, discord.Embed, FILE)):
                    data = [data]

                content = None
                embed = None
                files = []
                for item in data:
                    if isinstance(item, str):
                        content = item
                    elif isinstance(item, discord.Embed):
                        embed = item
                    else:
                        files.append(item)

                data = TextMessageData(content, embed, files)

        super().__init__(start_period, end_period, data, start_in, remove_after, period)
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
                self._event_ctrl.emit(EventID._trigger_message_remove, self.parent, self)


    def generate_log_context(self,
                             success_context: Dict[str, Union[bool, Optional[Exception]]],
                             content: Optional[str],
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
        if content is not None:
            sent_data_context["text"] = content
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

    def _verify_data(self, data: dict) -> bool:
        return super()._verify_data(TextMessageData, data)

    async def _send_channel(self,
                            content: Optional[str],
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
                        content,
                        embed=embed,
                        files=[discord.File(fwFILE.stream, fwFILE.filename) for fwFILE in files]
                    )

                # Mode is edit and message was already send to this channel
                elif self.mode == "edit":
                    await self.previous_message.edit(content, embed=embed)

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
        data_to_send = await self._data.to_dict()
        if self._verify_data(data_to_send):
            channel_ctx = await self._send_channel(**data_to_send)
            self._update_state()
            if channel_ctx["success"] is False:
                reason = channel_ctx["reason"]
                if isinstance(reason, discord.HTTPException):
                    if reason.status in {400, 403}:  # Bad request, forbidden
                        self._event_ctrl.emit(EventID._trigger_server_remove, self.parent)
                    elif reason.status == 401:  # Unauthorized (invalid token)
                        self._event_ctrl.emit(EventID.g_account_expired, self.parent.parent)

            return self.generate_log_context(channel_ctx, **data_to_send)

        return None

    def update(self, _init_options: Optional[dict] = None, **kwargs) -> asyncio.Future:
        return self._event_ctrl.emit(EventID._trigger_message_update, self, _init_options, **kwargs)

    async def _on_update(self, _, _init_options: Optional[dict], **kwargs):
        await self._close()
        if "start_in" not in kwargs:
            # This parameter does not appear as attribute, manual setting necessary
            kwargs["start_in"] = None

        if "start_period" not in kwargs:  # DEPRECATED, TODO: REMOVE IN FUTURE
            kwargs["start_period"] = None

        if "end_period" not in kwargs:  # DEPRECATED, TODO: REMOVE IN FUTURE
            kwargs["end_period"] = None

        if "data" not in kwargs:
            kwargs["data"] = self._data

        if _init_options is None:
            _init_options = {"parent": self.parent, "guild": self.dm_channel, "event_ctrl": self._event_ctrl}

        try:
            await async_util.update_obj_param(self, init_options=_init_options, **kwargs)
        except Exception:
            await self.initialize(self.parent, self._event_ctrl, self.dm_channel)
            raise
