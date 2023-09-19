"""
    Contains base definitions for different message classes.
"""

from typing import Any, Set, List, Iterable, Union, TypeVar, Optional, Dict, Callable
from functools import partial
from datetime import timedelta, datetime
from typeguard import check_type, typechecked
from enum import Enum, auto

from ..dtypes import *
from ..events import *
from ..logging.tracing import trace, TraceLEVELS
from ..misc import doc, attributes, async_util, instance_track

import random
import re
import copy
import asyncio
import _discord as discord


__all__ = (
    "BaseMESSAGE",
    "AutoCHANNEL",
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


class BaseMESSAGE:
    """
    This is the base class for all the different classes that
    represent a message you want to be sent into discord.

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
        "period",
        "start_period",
        "end_period",
        "next_send_time",
        "_data",
        "_fbcdata",
        "update_semaphore",
        "parent",
        "remove_after",
        "_created_at",
        "_timer_handle",
        "_event_ctrl",
    )

    @typechecked
    def __init__(self,
                 start_period: Optional[Union[int, timedelta]],
                 end_period: Union[int, timedelta],
                 data: Any,
                 start_in: Optional[Union[timedelta, datetime]],
                 remove_after: Optional[Union[int, timedelta, datetime]]):
        # Data parameter checks
        if isinstance(data, Iterable):
            if not len(data):
                raise TypeError(f"data parameter cannot be an empty iterable. Got: '{data}.'")

            annots = self.__init__.__annotations__["data"]
            for element in data:
                if isinstance(element, _FunctionBaseCLASS):  # Check if function is being used standalone
                    raise TypeError(f"{element} can be only used directly (data={element}()), not in a iterable.")

                # Check if the list elements are of correct type (typeguard does not protect iterable's elements)
                check_type("data", element, annots)

        # Deprecated int since v2.1
        if isinstance(start_period, int):
            trace("Using int on start_period is deprecated, use timedelta object instead.", TraceLEVELS.DEPRECATED)
            start_period = timedelta(seconds=start_period)

        if isinstance(end_period, int):
            trace("Using int on end_period is deprecated, use timedelta object instead.", TraceLEVELS.DEPRECATED)
            end_period = timedelta(seconds=end_period)

        if isinstance(start_period, timedelta) and start_period >= end_period:
            raise ValueError("'start_period' must be less than 'end_period'")

        # Clamp periods to minimum level (prevent infinite loops)
        self.start_period = None if start_period is None else max(start_period, timedelta(seconds=C_PERIOD_MINIMUM_SEC))
        self.end_period = max(end_period, timedelta(seconds=C_PERIOD_MINIMUM_SEC))
        self.period = self.end_period  # This can randomize in _reset_timer

        if isinstance(start_in, datetime):
            self.next_send_time = start_in
        else:
            self.next_send_time = datetime.now() + start_in

        self.parent = None  # The xGUILD object this message is in (needed for update method).
        self.remove_after = remove_after  # Remove the message from the list after this
        self._created_at = datetime.now()
        self._data = data
        self._fbcdata = isinstance(data, _FunctionBaseCLASS)
        self._timer_handle: asyncio.Task = None
        self._event_ctrl: EventController = None
        # Attributes created with this function will not be re-referenced to a different object
        # if the function is called again, ensuring safety (.update_method)
        attributes.write_non_exist(self, "update_semaphore", asyncio.Semaphore(1))
        # For comparing copies of the object (prevents .update from overwriting)
        attributes.write_non_exist(self, "_id", id(self))

    def __repr__(self) -> str:
        return f"{type(self).__name__}(data={self._data})"

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
        for slot in attributes.get_all_slots(type(self)):
            self_val = getattr(self, slot)
            if isinstance(self_val, (asyncio.Semaphore, asyncio.Lock)):
                # Hack to copy semaphores since not all of it can be copied directly
                copied = type(self_val)(self_val._value)
            else:
                copied = copy.deepcopy((self_val))

            setattr(new, slot, copied)

        return new

    @property
    def remaining_before_removal(self) -> Any:
        """
        Returns the remaining send counts / date after which
        the message will be removed from the sending list.

        .. versionadded:: v2.10
        """
        r = self.remove_after
        if isinstance(r, timedelta):
            r = r - (datetime.now() - self._created_at)

        return r

    @property
    def created_at(self) -> datetime:
        "Returns the datetime of when the object was created"
        return self._created_at

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

    def _check_state(self) -> bool:
        """
        Checks if the message is ready to be deleted.
        This is extended in subclasses.

        Returns
        ----------
        True
            The message should be deleted.
        False
            The message is in proper state, do not delete.
        """
        # Check remove_after
        type_ = type(self.remove_after)
        return (
            type_ is timedelta and datetime.now() - self._created_at > self.remove_after or
            type_ is datetime and datetime.now() > self.remove_after
        )

    def _update_state(self):
        """
        Updates the internal counter for auto-removal
        This is extended in subclasses.
        """
        raise NotImplementedError

    def _generate_exception(self,
                            status: int,
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

    def generate_log_context(self):
        """
        This method is used for generating a dictionary (later converted to json) of the
        data that is to be included in the message log. This is to be implemented inside the
        inherited classes.
        """
        raise NotImplementedError

    async def _get_data(self) -> dict:
        """
        Returns a dictionary of keyword arguments that is then expanded
        into other functions (_send_channel, _generate_log)
        This is to be additionally implemented in inherited classes due to different data_types

        .. versionchanged:: v2.3
            Turned async.
        """
        if self._fbcdata:
            return await self._data.retrieve()

        return self._data

    def _handle_error(self) -> bool:
        """
        This method handles the error that occurred during the execution of the function.
        Returns ``True`` if error was handled.
        """
        raise NotImplementedError

    def _is_ready(self) -> bool:
        """
        This method returns bool indicating if message is ready to be sent.
        """
        return datetime.now() >= self.next_send_time

    def _calc_next_time(self):
        if self.start_period is not None:
            range = map(int, [self.start_period.total_seconds(), self.end_period.total_seconds()])
            self.period = timedelta(seconds=random.randrange(*range))

        # Absolute timing instead of relative to prevent time slippage due to missed timer reset.
        current_stamp = datetime.now()
        while self.next_send_time < current_stamp:
            self.next_send_time += self.period

    def _reset_timer(self) -> None:
        """
        Resets internal timer.
        """
        self._calc_next_time()
        self._timer_handle = async_util.call_at(
            self._event_ctrl.emit,
            self.next_send_time,
            EventID.message_ready, self.parent, self
        )

    async def _send_channel(self) -> dict:
        """
        Sends data to a specific channel, this is separate from send
        for easier implementation of similar inherited classes
        The method returns a dictionary: `{"success": bool, "reason": discord.HTTPException}` where
        `"reason"` is only present if `"success"` `is False`
        """
        raise NotImplementedError

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
            self.next_send_time,
            EventID.message_ready, self.parent, self
        )

        event_ctrl.add_listener(
            EventID.message_update,
            self._on_update,
            lambda message, *args, **kwargs: message is self
        )

    async def _on_update(self, _, _init_options: Optional[dict], **kwargs):
        raise NotImplementedError
    
    @async_util.with_semaphore("update_semaphore")
    async def _close(self):
        """
        Closes the timer handles.
        """
        if self._timer_handle is not None and not self._timer_handle.cancelled():
            self._timer_handle.cancel()
            await asyncio.gather(self._timer_handle, return_exceptions=True)

        self._event_ctrl.remove_listener(EventID.message_update, self._on_update)


@instance_track.track_id
@doc.doc_category("Auto objects", path="message")
class AutoCHANNEL:
    """
    .. versionadded:: v2.3

    .. versionchanged:: v2.10

        :py:meth:`daf.message.AutoCHANNEL.remove` will now
        prevent the channel from being readded again.

    Used for creating instances of automatically managed channels.
    The objects created with this will automatically add new channels
    at creation and dynamically while the framework is already running,
    if they match the patterns.

    .. code-block:: python
       :caption: Usage
       :emphasize-lines: 4

       # TextMESSAGE is used here, but works for others too
       daf.message.TextMESSAGE(
            ..., # Other parameters
            channels=daf.message.AutoCHANNEL(...)
        )


    Parameters
    --------------
    include_pattern: str
        Regex pattern to match for the channel to be considered.

        For example you can do write ``.*`` to match ALL channels you are joined into or specify
        (parts of) channel names separated with ``|`` like so: "name1|name2|name3|name4"
    exclude_pattern: str
        Regex pattern to match for the channel to be excluded
        from the consideration.

        .. note::
            If both include_pattern and exclude_pattern yield a match, the guild will be
            excluded from match.

    interval: Optional[timedelta] = timedelta(minutes=5)
        Interval at which to scan for new channels.
    """

    __slots__ = (
        "include_pattern",
        "exclude_pattern",
        "parent",
        "removed_channels",
        "channel_getter",
        "_cache"
    )

    def __init__(
        self,
        include_pattern: str,
        exclude_pattern: Optional[str] = None
    ) -> None:
        # Remove spaces around OR
        self.include_pattern = re.sub(r"\s*\|\s*", '|', include_pattern) if include_pattern else None
        self.exclude_pattern = re.sub(r"\s*\|\s*", '|', exclude_pattern) if exclude_pattern else None
        self.parent = None
        self.channel_getter: Callable = None
        self.removed_channels: Set[int] = set()
        self._cache = []

    def __iter__(self):
        "Returns the channel iterator."
        return iter(self._get_channels())

    def __len__(self):
        "Returns number of channels found."
        return len(self._cache)

    def __bool__(self) -> bool:
        "Prevents removal of xMESSAGE by always returning True"
        return True

    @property
    def channels(self) ->  List[ChannelType]:
        "Return a list of found channels"
        return self._cache[:]

    def _get_channels(self) -> List[ChannelType]:
        """
        Property that returns a list of :class:`discord.TextChannel` or :class:`discord.VoiceChannel`
        (depends on the xMESSAGE type this is in) objects in cache.
        """
        channel: ChannelType
        _found = []
        for channel in self.channel_getter():
            if channel.id not in self.removed_channels:
                if (member := channel.guild.get_member(channel._state.user.id)) is None:  # Invalid intents?
                    return

                perms = channel.permissions_for(member)
                name = channel.name
                if (
                    (perms.send_messages or (perms.connect and perms.stream and perms.speak)) and
                    re.search(self.include_pattern, name) is not None and
                    (self.exclude_pattern is None or re.search(self.exclude_pattern, name) is None)
                ):
                    _found.append(channel)

        self._cache = _found
        return _found

    async def initialize(self, parent, channel_getter: Callable):
        """
        Initializes async parts of the instance.
        This method should be called by ``parent``.

        .. versionchanged:: v2.10

            Changed the channel ``channel_type`` into ``channel_getter``, which is now
            a function that can be used to get a list of all the correct channels.

        Parameters
        -----------
        parent: message.BaseMESSAGE
            The message object this AutoCHANNEL instance is in.
        channel_type: str
            The channel type to look for when searching for channels
        """
        self.parent = parent
        self.channel_getter = channel_getter

    def remove(self, channel: ChannelType):
        """
        Removes channel from cache.

        Parameters
        -----------
        channel: Union[discord.TextChannel, discord.VoiceChannel]
            The channel to remove from cache.

        Raises
        -----------
        KeyError
            The channel is not in cache.
        """
        self.removed_channels.add(channel.id)

    async def update(self, init_options = None, **kwargs):
        """
        Updates the object with new initialization parameters.

        Parameters
        ------------
        kwargs: Any
            Any number of keyword arguments that appear in the
            object initialization.

        Raises
        -----------
        Any
            Raised from :py:meth:`~daf.message.AutoCHANNEL.initialize` method.
        """
        if init_options is None:
            init_options = {}
            init_options["parent"] = self.parent
            init_options["channel_getter"] = self.channel_getter

        return await async_util.update_obj_param(self, init_options=init_options, **kwargs)


class BaseChannelMessage(BaseMESSAGE):
    """
    .. versionadded:: v2.10

    Message base for message types that have channels.
    """
    __slots__ = (
        "channels",
        "channel_getter",
        "remove_after_by_channel"
    )

    @typechecked
    def __init__(
        self,
        start_period: Union[timedelta, int, None],
        end_period: Union[int, timedelta],
        data: Any,
        channels: Union[List[Union[int, ChannelType]], AutoCHANNEL],
        start_in: Optional[Union[timedelta, datetime]] = timedelta(seconds=0),
        remove_after: Optional[Union[int, timedelta, datetime]] = None
    ):
        super().__init__(start_period, end_period, data, start_in, remove_after)
        self.channels = channels
        self.channel_getter = None
        # Override the default remove_after logic if it's an integer.
        self.remove_after_by_channel = {}

    @property
    def remaining_before_removal(self) -> Union[Dict[ChannelType, int], timedelta, datetime, int]:
        """
        Returns
        ------------
        int
            (Only if message not yet sent) Number of successful sends to each channel before removal.
        Dict[ChannelType, int]
            Dictionary mapping channel objects to remaining number of sends to that channel.
        timedelta
            Remaining ammount of time before removal.
        datetime
            Timestamp of removal.
        """
        return {self.parent.parent.client.get_channel(k): v for k, v in self.remove_after_by_channel.items()} or super().remaining_before_removal

    @typechecked
    def update(self, _init_options: Optional[dict] = None, **kwargs: Any) -> asyncio.Future:
        return self._event_ctrl.emit(EventID.message_update, self, _init_options, **kwargs)

    def _check_state(self) -> bool:
        return (
            super()._check_state() or
            # 'or [True]' assures this evaluates to False if the map is empty (no channels were ever advertised)
            type(self.remove_after) is int and not any(self.remove_after_by_channel.values() or [True]) or
            not bool(self.channels)
        )

    def _update_state(self, succeeded_channels: List[ChannelType], err_channels: List[dict]):
        "Updates internal remove_after counter and checks if any channels need to be remove."

        # Override the default counter remove_after behaviour to act independant on separate channels.
        if isinstance(self.remove_after, int):
            for channel in succeeded_channels:
                snowflake = channel.id
                if snowflake not in self.remove_after_by_channel:
                    self.remove_after_by_channel[snowflake] = self.remove_after

                self.remove_after_by_channel[snowflake] -= 1
                if not self.remove_after_by_channel[snowflake]:  # No more tries left
                    trace(
                        f"Removing channel '{channel.name}' ({channel.id}) [Guild '{channel.guild.name}' ({channel.guild.id})] from {self} - 'remove_after' sends reached.",
                        TraceLEVELS.NORMAL,
                    )
                    self.channels.remove(channel)

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

    async def initialize(
        self,
        parent: Any,
        event_ctrl: EventController,
        channel_types: Set,
        channel_getter: Callable
    ):
        """
        This method initializes the implementation specific API objects and
        checks for the correct channel input context.

        Parameters
        --------------
        parent: daf.guild.GUILD
            The GUILD this message is in
        channel_types: List
            List of allowed channel types.

        Raises
        ------------
        TypeError
            Channel contains invalid channels
        ValueError
            Channel does not belong to the guild this message is in.
        ValueError
            No valid channels were passed to object"
        """
        if parent is None:
            raise RuntimeError(f"No parent was passed to ({self})!")

        ch_i = 0
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
                    trace(f"Unable to get channel from ID {channel_id}", TraceLEVELS.WARNING)
                    to_remove.append(channel)
                elif type(channel) not in channel_types:
                    raise TypeError(f"{type(self).__name__} object received invalid channel type of {type(channel).__name__}")
                elif channel not in channel_getter():
                    raise ValueError(
                        f"{channel.name}(ID: {channel_id}) not in {channel.guild.name}(ID: {channel.guild.id}), "
                        f"but is part of {channel.guild.name}(ID: {channel.guild.id})"
                    )

            for channel in to_remove:
                self.channels.remove(channel)

            if not self.channels:
                raise ValueError(f"No valid channels were passed to {self} object")

        self.parent = parent
        await super().initialize(event_ctrl)

    @async_util.with_semaphore("update_semaphore")
    async def _send(self):
        """
        Sends the data into the channels.
        """
        # Acquire mutex to prevent update method from writing while sending
        data_to_send = await self._get_data()
        if any(data_to_send.values()):  # There is data to be send
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
            kwargs["start_in"] = self.next_send_time

        if "data" not in kwargs:
            kwargs["data"] = self._data

        kwargs["channels"] = channels = kwargs.get("channels", self.channels)
        if isinstance(channels, AutoCHANNEL):
            await channels.update(init_options={"parent": self, "channel_getter": self.channel_getter})
        elif not isinstance(self.channels[0], int):  # Not initialized (newly created):
            kwargs["channels"] = [x.id for x in self.channels]

        if _init_options is None:
            _init_options = {
                "parent": self.parent,
                "channel_getter": self.channel_getter,
                "event_ctrl": self._event_ctrl
            }

        await async_util.update_obj_param(self, init_options=_init_options, **kwargs)
