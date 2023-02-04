"""
    Contains base definitions for different message classes."""

from contextlib import suppress
from typing import Any, Set, List, Iterable, Union, TypeVar, Optional
from datetime import timedelta, datetime
from typeguard import check_type, typechecked

from ..dtypes import *
from ..logging.tracing import *
from ..timing import *
from .. import misc
from .. import client

import random
import re
import copy
import asyncio
import _discord as discord


__all__ = (
    "BaseMESSAGE",
    "AutoCHANNEL",
)

T = TypeVar("T")
ChannelType = Union[discord.TextChannel, discord.VoiceChannel]

# Configuration
# ----------------------
C_PERIOD_MINIMUM_SEC = 1 # Minimal seconds the period can be

class BaseMESSAGE:
    """
    This is the base class for all the different classes that
    represent a message you want to be sent into discord.

    .. deprecated:: v2.1

        - start_in (start_now) - Using bool value to dictate whether the message should be sent at framework start.
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
        If start_period is not None, this dictates the upper limit for range of the randomized period. If start_period is None, then this
                            dictates a fixed sending period in SECONDS, eg. if you pass the value `5`, that means the message will be sent every 5 seconds.
    data: inherited class dependant
        The data to be sent to discord.
    start_in: timedelta
        When should the message be first sent.
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
        "_deleted"
    )

    @typechecked
    def __init__(self,
                start_period: Optional[Union[int, timedelta]],
                end_period: Union[int, timedelta],
                data: Any,
                start_in: Union[timedelta, bool],
                remove_after: Optional[Union[int, timedelta, datetime]]):
        # Data parameter checks
        if isinstance(data, Iterable):
            if not len(data):
                raise TypeError(f"data parameter cannot be an empty iterable. Got: '{data}.'")
            
            annots = self.__init__.__annotations__["data"]  
            for element in data:
                if isinstance(element, _FunctionBaseCLASS): # Check if function is being used standalone
                    raise TypeError(f"The function can only be used on the data parameter directly, not in a iterable. Function: '{element}).'")
                
                # Check if the list elements are of correct type (typeguard does not protect iterable's elements)
                check_type("data", element, annots)

        # Deprecated int since v2.1
        if isinstance(start_period, int):
            trace("Using int on start_period is deprecated, use timedelta object instead.", TraceLEVELS.DEPRECATED)
            start_period = timedelta(seconds=start_period)

        if isinstance(end_period, int):
            trace("Using int on end_period is deprecated, use timedelta object instead.", TraceLEVELS.DEPRECATED)
            end_period = timedelta(seconds=end_period)
                
        # Clamp periods to minimum level (prevent infinite loops)
        self.start_period = None if start_period is None else max(start_period, timedelta(seconds=C_PERIOD_MINIMUM_SEC))
        self.end_period = max(end_period, timedelta(seconds=C_PERIOD_MINIMUM_SEC))
        self.period = self.end_period # This can randomize in _reset_timer

        # Deprecated bool since v2.1
        if isinstance(start_in, bool): 
            self.next_send_time = datetime.now() if start_in else datetime.now() + self.end_period
            trace("Using bool value for 'start_in' ('start_now') parameter is deprecated. Use timedelta object instead.", TraceLEVELS.DEPRECATED)
        else:
            self.next_send_time = datetime.now() + start_in

        self.parent = None # The xGUILD object this message is in (needed for update method).
        self.remove_after = remove_after # Remove the message from the list after this
        self._created_at = datetime.now()
        self._data = data
        self._fbcdata = isinstance(data, _FunctionBaseCLASS)
        self._deleted = False
        # Attributes created with this function will not be re-referenced to a different object
        # if the function is called again, ensuring safety (.update_method)
        misc._write_attr_once(self, "update_semaphore", asyncio.Semaphore(1))
        # For comparing copies of the object (prevents .update from overwriting)
        misc._write_attr_once(self, "_id", id(self))

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
        for slot in list(self.__slots__) + list(BaseMESSAGE.__slots__):
            self_val = getattr(self, slot)
            if isinstance(self_val, (asyncio.Semaphore, asyncio.Lock)):
                # Hack to copy semaphores since not all of it can be copied directly
                copied = type(self_val)(self_val._value)
            else:
                copied = copy.deepcopy((self_val))

            setattr(new, slot, copied)

        return new

    @property
    def created_at(self) -> datetime:
        "Returns the datetime of when the object was created"
        return self._created_at

    @property
    def deleted(self) -> bool:
        """
        Returns
        -----------
        True
            The object is no longer in the framework and should no longer
            be used.
        False
            Object is in the framework in normal operation.
        """
        return self._deleted
    
    def _delete(self):
        """
        Sets the internal _deleted flag to True,
        indicating the object should not be used.
        """
        self._deleted = True

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
        return (type_ is int and self.remove_after == 0 or
                type_ is timedelta and datetime.now() - self._created_at > self.remove_after or # The difference from creation time is bigger than remove_after
                type_ is datetime and datetime.now() > self.remove_after) # The current time is larger than remove_after
    
    def _update_state(self):
        """
        Updates the internal counter for auto-removal
        This is extended in subclasses.
        """
        if type(self.remove_after) is int:
            self.remove_after -= 1

    def _generate_exception(self,
                           status: int,
                           code: int,
                           description: str,
                           cls: T) -> T:
        """
        Generates a discord.HTTPException inherited class exception object.
        This is used for generating dummy exceptions that are then raised inside the `._send_channel()`
        method to simulate what would be the result of a API call, without actually having to call the API (reduces the number of bad responses).

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
        resp = cls(resp, {"message" : description, "code" : code})
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

    def _reset_timer(self) -> None:
        """
        Resets internal timer
        """
        if self.start_period is not None:
            range = map(int, [self.start_period.total_seconds(), self.end_period.total_seconds()])
            self.period = timedelta(seconds=random.randrange(*range))

        # Absolute timing instead of relative to prevent time slippage due to missed timer reset.
        current_stamp = datetime.now()
        while self.next_send_time < current_stamp:
            self.next_send_time += self.period

    async def _send_channel(self) -> dict:
        """
        Sends data to a specific channel, this is separate from send
        for easier implementation of similar inherited classes
        The method returns a dictionary: `{"success": bool, "reason": discord.HTTPException}` where
        `"reason"` is only present if `"success"` `is False`
        """
        raise NotImplementedError

    async def _send(self) -> dict:
        """
        Sends a message to all the channels.
        Returns a dictionary generated by the `.generate_log_context` method
        """
        raise NotImplementedError

    async def initialize(self, **options):
        """
        This method initializes the implementation specific
        api objects and checks for the correct channel input context.
        """
        raise NotImplementedError

    async def update(self, _init_options: dict={}, **kwargs):
        """
        Used for changing the initialization parameters the object was initialized with.

        .. warning::
            Upon updating, the internal state of objects get's reset, meaning you basically have a brand new created object.

        Parameters
        -------------
        init_options: dict
            Contains the initialization options used in .initialize() method for re-initializing certain objects.
            This is implementation specific and not necessarily available.
        original_params:
            The allowed parameters are the initialization parameters first used on creation of the object AND

        Raises
        ------------
        TypeError
            Invalid keyword argument was passed
        Other
            Raised from .initialize() method

        .. versionadded::
            v2.0
        """

        raise NotImplementedError

@misc.doc_category("Auto objects", path="message")
class AutoCHANNEL:
    """
    .. versionadded:: v2.3

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
        "interval",
        "parent",
        "cache",
        "channel_getter",
        "last_scan"
    )
    def __init__(self,
                 include_pattern: str,
                 exclude_pattern: Optional[str] = None,
                 interval: Optional[timedelta] = timedelta(minutes=5)) -> None:
        self.include_pattern = include_pattern
        self.exclude_pattern = exclude_pattern
        self.interval = interval.total_seconds()
        self.parent = None
        self.channel_getter: property = None
        self.cache: Set[ChannelType] = set()
        self.last_scan = 0

    def __iter__(self):
        "Returns the channel iterator."
        self._process()
        return iter(self.channels)

    def __bool__(self) -> bool:
        "Prevents removal of xMESSAGE by always returning True"
        return True

    @property
    def channels(self) -> List[ChannelType]:
        """
        Property that returns a list of :class:`discord.TextChannel` or :class:`discord.VoiceChannel`
        (depends on the xMESSAGE type this is in) objects in cache.
        """
        return list(self.cache)

    async def initialize(self, parent, channel_type: str):
        """
        Initializes async parts of the instance.
        This method should be called by ``parent``.

        Parameters
        -----------
        parent: message.BaseMESSAGE
            The message object this AutoCHANNEL instance is in.
        channel_type: str
            The channel type to look for when searching for channels
        """
        self.parent = parent
        self.channel_getter = channel_type

    def _process(self):
        """
        Task that scans and adds new channels to cache.
        """
        channel: ChannelType
        stamp = datetime.now().timestamp()
        if stamp - self.last_scan > self.interval:
            self.last_scan = stamp
            guild: discord.Guild = self.parent.parent.apiobject
            client_: discord.Client = self.parent.parent.parent.client
            member = guild.get_member(client_.user.id)

            # Possible intents bug?
            if member is None:
                return
            
            # User has not verified / has not completed rules
            if guild.me.pending:
                return

            for channel in getattr(guild, self.channel_getter):
                if channel not in self.cache:
                    perms = channel.permissions_for(member)
                    name = channel.name
                    if ((perms.send_messages or (perms.connect and perms.stream and perms.speak)) and
                        re.search(self.include_pattern, name) is not None and
                        (self.exclude_pattern is None or re.search(self.exclude_pattern, name) is None)
                    ):
                        self.cache.add(channel)

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
        self.cache.remove(channel)

    async def update(self, **kwargs):
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
        if "interval" not in kwargs:
            kwargs["interval"] = timedelta(seconds=self.interval)
        
        return await misc._update(self,
                                  init_options={"parent": self.parent, "channel_type": self.channel_getter},
                                  **kwargs)
