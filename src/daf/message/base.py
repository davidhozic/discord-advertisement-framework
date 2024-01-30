"""
    Contains base definitions for different message classes.
"""
from typing import Any, Set, List, Union, TypeVar, Optional, Dict, Callable, get_type_hints
from datetime import timedelta, datetime
from abc import ABC, abstractmethod
from typeguard import typechecked
from functools import partial
from enum import Enum, auto

from ..logging.tracing import trace, TraceLEVELS
from ..misc import doc, attributes, async_util
from ..messagedata import BaseMessageData
from .autochannel import AutoCHANNEL
from .messageperiod import *
from ..dtypes import *
from ..events import *

import _discord as discord
import asyncio
import copy


__all__ = (
    "BaseMESSAGE",
    "ChannelErrorAction",
    "BaseChannelMessage",
)


T = TypeVar("T")
ChannelType = Union[discord.TextChannel, discord.Thread, discord.VoiceChannel]

# Configuration
# ----------------------
C_PERIOD_MINIMUM_SEC = 1  # Minimal seconds the period can be


class ChannelErrorAction(Enum):
    """
    Used as a message's channel send error action
    """
    REMOVE_ACCOUNT = 0
    SKIP_CHANNELS = auto()


class BaseMESSAGE(ABC):
    """
    This is the base class for all the different classes that
    represent a message you want to be sent into discord.


    .. versionchanged:: v3.0
    
        - New ``remove_after`` property.
        - Removed ``remaining_before_removal`` property.

    .. deprecated:: v2.1

        - start_period, end_period - Using int values, use ``timedelta`` object instead.

    .. versionchanged:: v2.1

        - start_period, end_period Accept timedelta objects.
        - start_now - renamed into ``start_in`` which describes when the message should be first sent.
        - removed ``deleted`` property

    Parameters
    -----------------
    start_period: Union[int, timedelta, None]
        If this this is not None, then it dictates the bottom limit for range of the randomized period. Set this to None
                                         for a fixed sending period.
    end_period: Union[int, timedelta],
        If start_period is not None, this dictates the upper limit for range of the randomized period.
        If start_period is None, then this dictates a fixed sending period in SECONDS,
        eg. if you pass the value `5`, that means the message will be sent every 5 seconds.
    data: inherited class dependant
        The data to be sent to discord.
    start_in: Optional[timedelta | datetime]
        When should the message be first sent.
        *timedelta* means the difference from current time, while *datetime* means actual first send time.
    remove_after: Optional[Union[int, timedelta, datetime]]
        Deletes the message after:

        * int - provided amounts of sends
        * timedelta - the specified time difference
        * datetime - specific date & time
    """
    __slots__ = (
        "_id",
        "_data",
        "update_semaphore",
        "parent",
        "_remove_after",
        "_timer_handle",
        "_removal_timer",
        "_event_ctrl",
        "period",
    )
    def __init__(
        self,
        start_period: Optional[Union[int, timedelta]],
        end_period: Union[int, timedelta],
        data: BaseMessageData,
        start_in: Optional[Union[timedelta, datetime]],
        remove_after: Optional[Union[int, timedelta, datetime]],
        period: BaseMessagePeriod
    ):

        if isinstance(start_period, int):
            start_period = timedelta(seconds=start_period)

        if isinstance(end_period, int):
            end_period = timedelta(seconds=end_period)

        # Due to compatibility when adding the new 'period' parameter, some parameters needed default
        # values. The default values are all None for those parameters.
        if (
            end_period is None and period is None or
            start_period is not None and end_period is None
        ):
            raise TypeError(f"{type(self).__name__} missing required parameter 'period'")

        if start_period is not None and start_period >= end_period:
            raise ValueError("'start_period' must be less than 'end_period'")

        if end_period is not None:
            trace(
                "'start_period' and 'end_period' are deprecated and will be removed in v4.2.0."
                " Use 'period' instead.",
                TraceLEVELS.DEPRECATED
            )

            if period is None:
                if start_in is not None:
                    trace(
                        f"'start_in' parameter is deprecated in {type(self).__name__}. "
                        " Use the 'period' parameter to set both period and initial sending time.",
                        TraceLEVELS.DEPRECATED
                    )
                    if isinstance(start_in, datetime):
                        start_in = start_in.astimezone()
                    else:
                        start_in = datetime.now().astimezone() + start_in

                if start_period is None:
                    period = FixedDurationPeriod(end_period, start_in)
                else:
                    period = RandomizedDurationPeriod(start_period, end_period, start_in)
            else:
                raise TypeError(
                    "Deprecated parameter 'start_period' / 'end_period' is given"
                    " alongside the new'period' parameter."
                    " DO NOT USE 'start_period' and 'end_period', they will be removed in the future."
                )

        elif start_in is not None:
            raise TypeError(
                "Deprecated parameter 'start_in' is given"
                " alongside the new 'period' parameter."
                " DO NOT USE 'start_in', it will be removed in the future."
            )

        self.parent = None  # The xGUILD object this message is in (needed for update method).
        self._remove_after = remove_after
        self._data = data
        self.period = period

        self._timer_handle: asyncio.Task = None
        self._removal_timer: asyncio.Task = None
        self._event_ctrl: EventController = None

        # Attributes created with this function will not be re-referenced to a different object
        # if the function is called again, ensuring safety (.update_method)
        attributes.write_non_exist(self, "update_semaphore", asyncio.Semaphore(1))
        # For comparing copies of the object (prevents .update from overwriting)
        attributes.write_non_exist(self, "_id", id(self))

    def __repr__(self) -> str:
        data_str = str(self._data)[:30].strip("'")
        return f"{type(self).__name__}(data='{data_str}')"

    def __eq__(self, o: object) -> bool:
        """
        Compares two message objects.

        Parameters
        ------------
        o: BaseMESSAGE
            The message to compare this instance with.

        Raises
        ----------
        TypeError
            Parameter of incorrect type.
        """
        if isinstance(o, BaseMESSAGE):
            return o._id == self._id

        raise TypeError(f"Comparison of {type(self)} not allowed with {type(o)}")

    def __deepcopy__(self, *args):
        "Duplicates the object (for use in AutoGUILD)"
        new = copy.copy(self)
        new.parent = None  # Prevent loops and pickling issues
        for slot in attributes.get_all_slots(type(self)):
            self_val = getattr(new, slot)
            if isinstance(self_val, (asyncio.Semaphore, asyncio.Lock)):
                # Hack to copy semaphores since not all of it can be copied directly
                copied = type(self_val)(self_val._value)
            else:
                copied = copy.deepcopy(self_val)

            setattr(new, slot, copied)

        return new

    @property
    def remove_after(self) -> Any:
        """
        .. versionadded:: v3.0

        Returns the remaining send counts / date after which
        the message will be removed from the sending list.
        """
        return self._remove_after

    @abstractmethod
    async def update(self, _init_options: dict = {}, **kwargs):
        """
        .. versionadded:: v2.0

        .. versionchanged:: v3.0
            Turned into async api.

        |ASYNC_API|

        Used for changing the initialization parameters the object was initialized with.

        .. warning::
            Upon updating, the internal state of objects get's reset,
            meaning you basically have a brand new created object.

        Parameters
        -------------
        **kwargs: Any
            Custom number of keyword parameters which you want to update,
            these can be anything that is available during the object creation.

        Returns
        --------
        Awaitable
            An awaitable object which can be used to await for execution to finish.
            To wait for the execution to finish, use ``await`` like so: ``await method_name()``.

        Raises
        -----------
        TypeError
            Invalid keyword argument was passed
        Other
            Raised from .initialize() method.
        """
        raise NotImplementedError

    @abstractmethod
    def _update_state(self):
        """
        Updates the internal counter for auto-removal
        This is extended in subclasses.
        """
        raise NotImplementedError

    @staticmethod
    def _generate_exception(status: int,
                            code: int,
                            description: str,
                            cls: T) -> T:
        """
        Generates a discord.HTTPException inherited class exception object.
        This is used for generating dummy exceptions that are then raised inside the `._send_channel()`
        method to simulate what would be the result of a API call,
        without actually having to call the API (reduces the number of bad responses).

        Parameters
        -------------
        status: int
            Discord status code of the exception.
        code: int
            Discord error code.
        description: str
            The textual description of the error.
        cls: discord.HTTPException
            Inherited class from discord.HTTPException to make exception from.
        """
        resp = Exception()
        resp.status = status
        resp.status_code = status
        resp.reason = cls.__name__
        resp = cls(resp, {"message": description, "code": code})
        return resp

    @abstractmethod
    def generate_log_context(self):
        """
        This method is used for generating a dictionary (later converted to json) of the
        data that is to be included in the message log. This is to be implemented inside the
        inherited classes.
        """
        raise NotImplementedError

    @abstractmethod
    def _handle_error(self) -> bool:
        """
        This method handles the error that occurred during the execution of the function.
        Returns ``True`` if error was handled.
        """
        raise NotImplementedError

    def _reset_timer(self) -> None:
        """
        Resets internal timer.
        """
        self._timer_handle = async_util.call_at(
            self._event_ctrl.emit,
            self.period.calculate(),
            EventID._trigger_message_ready, self.parent, self
        )

    @abstractmethod
    def _verify_data(self, type_: type[BaseMessageData], data: dict) -> bool:
        """
        Verifies is the data is valid. Returns True on successful verification.

        This needs to be subclassed and the subclass's method needs relay the call to this
        method, providing the type.

        Parameters
        ------------
        type_: type[BaseMessageData]
            The class representing the message data.
        data: dict
            The data being checked.
        """
        hints = get_type_hints(type_)
        if data is None or len(data) != len(hints):
            return False

        for k in hints:
            if k not in data:
                return False

        return True

    @abstractmethod
    async def _send_channel(self) -> dict:
        """
        Sends data to a specific channel, this is separate from send
        for easier implementation of similar inherited classes
        The method returns a dictionary: `{"success": bool, "reason": discord.HTTPException}` where
        `"reason"` is only present if `"success"` `is False`
        """
        raise NotImplementedError

    @abstractmethod
    async def _send(self) -> Union[Dict, None]:
        """
        Sends a message to all the channels.
        """
        raise NotImplementedError

    async def initialize(self, event_ctrl: EventController):
        """
        This method initializes the implementation specific
        api objects and checks for the correct channel input context.
        """
        self._event_ctrl = event_ctrl
        self._timer_handle = async_util.call_at(
            event_ctrl.emit,
            self.period.get(),
            EventID._trigger_message_ready, self.parent, self
        )
        self._event_ctrl.add_listener(
            EventID._trigger_message_update,
            self._on_update,
            lambda message, *args, **kwargs: message is self
        )

        # Calculate actual datetime of when the message is going to be removed,
        # so that the time can be viewed instead of just constantly returning the same timedelta object.
        if isinstance(self._remove_after, timedelta):
            self._remove_after = datetime.now().astimezone() + self._remove_after

        # Setup remove_after schedule (in case it is datetime)
        if isinstance(self._remove_after, datetime):
            self._removal_timer = async_util.call_at(
                event_ctrl.emit,
                self._remove_after,
                EventID._trigger_message_remove, self.parent, self
            )

    @abstractmethod
    async def _on_update(self, _, _init_options: Optional[dict], **kwargs):
        raise NotImplementedError
    
    @async_util.with_semaphore("update_semaphore")
    async def _close(self):
        """
        Closes the timer handles.
        """
        if self._event_ctrl is None:  # Message not initialized / already closed
            return

        if self._timer_handle is not None and not self._timer_handle.cancelled():
            self._timer_handle.cancel()
            await asyncio.gather(self._timer_handle, return_exceptions=True)

        if self._removal_timer is not None and not self._removal_timer.cancelled():
            self._removal_timer.cancel()
            await asyncio.gather(self._removal_timer, return_exceptions=True)

        self._event_ctrl.remove_listener(EventID._trigger_message_update, self._on_update)


class BaseChannelMessage(BaseMESSAGE):
    """
    .. versionadded:: v2.10

    Message base for message types that have channels.
    """
    __slots__ = (
        "channels",
        "channel_getter",
        "_remove_after_original"
    )
    def __init__(
        self,
        start_period: Union[timedelta, int, None] = None,
        end_period: Union[int, timedelta] = None,
        data: BaseMessageData = None,
        channels: Union[List[Union[int, ChannelType]], AutoCHANNEL] = None,
        start_in: Optional[Union[timedelta, datetime]] = None,
        remove_after: Optional[Union[int, timedelta, datetime]] = None,
        period: BaseMessagePeriod = None
    ):
        super().__init__(start_period, end_period, data, start_in, remove_after, period)

        # Due to compatibility when adding the new 'period' parameter, some parameters needed default
        # values. The default values are all None for those parameters.
        if (
            channels is None
        ):
            raise TypeError(f"{type(self).__name__} missing required parameter 'channels'")

        # Due to compatibility when adding the new 'period' parameter, some parameters needed default
        # values. The default values are all None for those parameters.
        if (
            data is None
        ):
            raise TypeError(f"{type(self).__name__} missing required parameter 'data'")

        self.channels = channels
        self.channel_getter = None

        # In case int was passed, we need to have an original value in case any additional
        # channels were added by AutoCHANNEL, as int in case of channel messages is defined
        # as maximum amount of successful sends into each channel separately.
        self._remove_after_original = remove_after
        if isinstance(self._remove_after, int):
            self._remove_after = {}

    @property
    def remove_after(self) -> Union[int, datetime, None]:
        """
        Returns the remaining send counts / date after which the message will be removed from the sending list.
        If the original type of the ``remove_after`` parameter to the message was of type int, this will
        return the maximum remaining amount of sends from all channels. If all the channels have been removed,
        this will return the original count ``remove_after`` parameter.
        """
        # An integer was originally provided, the dict is remove_after by each channel
        if isinstance(self._remove_after_original, int):
            return max(self._remove_after.values(), default=self._remove_after_original)

        return self._remove_after

    @typechecked
    def update(self, _init_options: Optional[dict] = None, **kwargs: Any) -> asyncio.Future:
        return self._event_ctrl.emit(EventID._trigger_message_update, self, _init_options, **kwargs)

    def _update_state(self, succeeded_channels: List[ChannelType], err_channels: List[dict]):
        "Updates internal remove_after counter and checks if any channels need to be remove."

        # Override the default counter remove_after behaviour to act independant on separate channels.
        if isinstance(self._remove_after_original, int):
            for channel in succeeded_channels:
                snowflake = channel.id
                if snowflake not in self._remove_after:
                    self._remove_after[snowflake] = self._remove_after_original

                self._remove_after[snowflake] -= 1
                if not self._remove_after[snowflake]:  # No more tries left
                    trace(
                        f"Removing channel '{channel.name}' ({channel.id}) [Guild '{channel.guild.name}' ({channel.guild.id})] from {self} - 'remove_after' sends reached.",
                        TraceLEVELS.NORMAL,
                    )
                    self.channels.remove(channel)
                    del self._remove_after[snowflake]

            # All channel counts expired + at least one succeeded channel.
            # If not succeeded channel was passed, then the counters could not decrement, meaning
            # message was never advertise. If message was never advertised then the remove_after counter is invalid.
            if not self._remove_after and succeeded_channels:
                self._event_ctrl.emit(EventID._trigger_message_remove, self.parent, self)
                # Prevent dual removal events, errored channels also don't need to be removed if the message is removed
                return

        # Remove any channels that returned with code status 404 (They no longer exist)
        for data in err_channels:
            reason = data["reason"]
            channel = data["channel"]
            if isinstance(reason, discord.HTTPException):
                if (
                    reason.status == 403 or  # Forbidden
                    reason.code in {50007, 10003}  # Not Forbidden, but bad error codes
                ):
                    trace(
                        f"Removing channel '{channel.name}' ({channel.id}) [Guild '{channel.guild.name}' ({channel.guild.id})], because user '{self.parent.parent.client.user.name}' lacks permissions.",
                        TraceLEVELS.WARNING
                    )
                    self.channels.remove(channel)

        if not self.channels:
            self._event_ctrl.emit(EventID._trigger_message_remove, self.parent, self)

    def _get_channel_types(self) -> Set[ChannelType]:
        "Returns a set of valid channels types. Implement in subclasses."
        raise NotImplementedError

    @async_util.except_return
    async def initialize(
        self,
        parent: Any,
        event_ctrl: EventController,
        channel_getter: Callable
    ):
        """
        This method initializes the implementation specific API objects and
        checks for the correct channel input context.

        Parameters
        --------------
        parent: daf.guild.GUILD
            The GUILD this message is in
        event_ctrl: EventController
            The ACCOUNT bound event controller.
        channel_getter: Callable
            Function for retrieving available channels.
        """
        ch_i = 0
        channel_types = self._get_channel_types()
        client: discord.Client = parent.parent.client
        to_remove = []
        self.channel_getter = channel_getter  # Store for purposes of update

        # Convert the channel_getter of all guild channels, into a getter of only the specific types
        channel_getter = partial(channel_getter, *channel_types)

        if isinstance(self.channels, AutoCHANNEL):
            await self.channels.initialize(self, channel_getter)
        else:
            for ch_i, channel in enumerate(self.channels):
                if isinstance(channel, discord.abc.GuildChannel):
                    channel_id = channel.id
                else:
                    # Snowflake IDs provided
                    channel_id = channel
                    channel = self.channels[ch_i] = client.get_channel(channel_id)

                if channel is None:
                    trace(f"Unable to get channel from ID {channel_id} - {self}", TraceLEVELS.ERROR)
                    to_remove.append(channel)
                elif type(channel) not in channel_types:
                    trace(
                        f"{self} received channel of invalid type: {channel}",
                        TraceLEVELS.ERROR
                    )
                    to_remove.append(channel)
                elif channel not in channel_getter():
                    trace(
                        f"{channel} is not part of the guild that message is in - {self}",
                        TraceLEVELS.ERROR
                    )
                    to_remove.append(channel)

            for channel in to_remove:
                self.channels.remove(channel)

            if not self.channels:
                trace(f"No valid channels passed to {self}.", TraceLEVELS.ERROR, exception_cls=ValueError)

        self.parent = parent
        return await super().initialize(event_ctrl)

    @async_util.with_semaphore("update_semaphore")
    async def _send(self):
        """
        Sends the data into the channels.
        """
        # Acquire mutex to prevent update method from writing while sending
        data_to_send = await self._data.to_dict()
        if self._verify_data(data_to_send):  # There is data to be send
            errored_channels = []
            succeeded_channels = []

            # Send to channels
            for channel in self.channels:
                # Clear previous messages sent to channel if mode is MODE_DELETE_SEND
                context = await self._send_channel(channel, **data_to_send)
                if context["success"]:
                    succeeded_channels.append(channel)
                else:
                    errored_channels.append({"channel": channel, "reason": context["reason"]})
                    action = context["action"]
                    if action is ChannelErrorAction.SKIP_CHANNELS:  # Don't try to send to other channels
                        break

                    elif action is ChannelErrorAction.REMOVE_ACCOUNT:
                        self._event_ctrl.emit(EventID.g_account_expired, self.parent.parent)
                        break

            self._update_state(succeeded_channels, errored_channels)
            if errored_channels or succeeded_channels:
                return self.generate_log_context(
                    **data_to_send, succeeded_ch=succeeded_channels, failed_ch=errored_channels
                )

        return None

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

        kwargs["channels"] = channels = kwargs.get("channels", self.channels)
        if isinstance(channels, AutoCHANNEL):
            await channels.update(init_options={"parent": self, "channel_getter": self.channel_getter})

        if _init_options is None:
            _init_options = {
                "parent": self.parent,
                "channel_getter": self.channel_getter,
                "event_ctrl": self._event_ctrl
            }

        try:
            await async_util.update_obj_param(self, init_options=_init_options, **kwargs)            
        except Exception:
            await self.initialize(self.parent, self._event_ctrl, self.channel_getter)
            raise
