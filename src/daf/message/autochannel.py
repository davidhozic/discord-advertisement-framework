from typing import Set, List, Union, Optional, Callable
from typeguard import typechecked

from ..misc import doc, async_util, instance_track
from ..logging.tracing import trace, TraceLEVELS

from ..logic import BaseLogic
from ..logic import *

import _discord as discord
import re


__all__ = ("AutoCHANNEL",)


ChannelType = Union[discord.TextChannel, discord.Thread, discord.VoiceChannel]


@instance_track.track_id
@doc.doc_category("Auto objects", path="message")
class AutoCHANNEL:
    """
    .. versionadded:: v2.3

    .. versionchanged:: v2.10

        :py:meth:`daf.message.AutoCHANNEL.remove` will now
        prevent the channel from being added again.

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
    include_pattern: BaseLogic
        Matching condition, which checks if the name of channels matches defined condition.
    """

    __slots__ = (
        "include_pattern",
        "parent",
        "removed_channels",
        "channel_getter",
        "_cache"
    )

    @typechecked
    def __init__(
        self,
        include_pattern: Union[BaseLogic, str],
        exclude_pattern: Optional[str] = None,
    ) -> None:
        if isinstance(include_pattern, str):
            trace(
                "Using text (str) on 'include_pattern' parameter of AutoGUILD is deprecated (planned for removal in 4.2.0)!\n"
                "Use logical operators instead (daf.logic). E. g., regex, contains, or_, ...\n",
                TraceLEVELS.DEPRECATED
            )
            include_pattern = regex(re.sub(r"\s*\|\s*", '', include_pattern))

        if exclude_pattern is not None:
            trace(
                "'exclude_pattern' parameter is deprecated (planned for removal in 4.2.0)!\n",
                TraceLEVELS.DEPRECATED
            )
            exclude_pattern = regex(re.sub(r"\s*\|\s*", '', exclude_pattern))
            include_pattern = and_(include_pattern, not_(exclude_pattern))

        self.include_pattern = include_pattern
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
    def channels(self) -> List[ChannelType]:
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
                    name is not None and
                    (perms.send_messages or (perms.connect and perms.stream and perms.speak)) and
                    self.include_pattern.check(name)
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

        if "exclude_pattern" not in kwargs: # DEPRECATED; TODO: remove in 4.2.0
            kwargs["exclude_pattern"] = None

        return await async_util.update_obj_param(self, init_options=init_options, **kwargs)
