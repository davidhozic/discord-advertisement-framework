"""
This module contains definitions related
to automatic generation of objects.
"""

from typing import Optional, Union, List, Dict
from datetime import datetime, timedelta
from typeguard import typechecked
from copy import deepcopy

from .logging.tracing import TraceLEVELS, trace

from . import misc
from . import guild
from . import message
from . import client

import re
import asyncio


__all__ = (
    "AutoGUILD",
)


class GLOBALS:
    "Contains global variables"


GUILD_GEN_REFRESH_INT = timedelta(minutes=1) # Default interval at which to scan for new guilds


@misc.doc_category("Automatic generation")
class AutoGUILD:
    """
    .. versionadded:: v2.3

    Used for creating instances that will return
    guild objects.

    .. warning::
        This will only automatically add new objects to the framework and not
        automatically remove them. That is up to the user to decide, use
        :py:func:`~daf.core.get_shill_list` to see added guilds.

    Parameters
    --------------
    include_pattern: str
        Regex pattern to use when searching guild names that are to be included.
    exclude_pattern: Optional[str] = None
        Regex pattern to use when searching guild names that are **NOT** to be excluded.

        .. note::
            If both include_pattern and exclude_pattern yield a match, the guild will be
            excluded from match.

    remove_after: Optional[Union[timedelta, datetime]] = None
        When to remove this object from the shilling list.
    logging: Optional[bool] = False
        Set to True if you want the guilds generated to log
        sent messages.
    interval: Optional[timedelta] = GUILD_GEN_REFRESH_INT
        Interval at which to scan for new guilds
    """
    __slots__ = (
        "include_pattern",
        "exclude_pattern",
        "remove_after",
        "messages",
        "logging",
        "interval",
        "cache",
        "task",
        "_created_at",
        "_deleted"
    )

    @typechecked
    def __init__(self,
                 include_pattern: str,
                 exclude_pattern: Optional[str] = None,
                 remove_after: Optional[Union[timedelta, datetime]] = None,
                 messages: Optional[List[message.BaseMESSAGE]] = [],
                 logging: Optional[bool] = False,
                 interval: Optional[timedelta] = GUILD_GEN_REFRESH_INT) -> None:
        self.include_pattern = include_pattern
        self.exclude_pattern = exclude_pattern
        self.remove_after = remove_after 
        self.messages = messages # Uninitialized template messages list that gets copied for each found guild.
        self.logging = logging
        self.interval = interval.total_seconds() # In seconds
        self.cache: Dict[guild.GUILD] = {}
        self.task = None # Holds the Task object of _find_guilds that needs to be cleaned upon garbage collection.
        self._deleted = False
        self._created_at = datetime.now()

    @property
    def guilds(self) -> List[guild.GUILD]:
        "Returns cached found GUILD objects."
        return list(self.cache.values())

    @property
    def created_at(self) -> datetime:
        """
        Returns the datetime of when the object has been created.
        """
        return self._created_at

    def _delete(self):
        """
        Sets the internal _deleted flag to True
        and cancels main task.
        """
        self._deleted = True
        self.task.cancel()

    def _check_state(self) -> bool:
        """
        Checks if the object is ready to be deleted.

        If the object has already been deleted, return False 
        to prevent multiple tasks from trying to remove it multiple
        times which would result in ValueError exceptions.

        Returns
        ----------
        True
            The object should be deleted.
        False
            The object is in proper state, do not delete.
        """
        if self._deleted:
            return False

        rm_after_type = type(self.remove_after)
        return (rm_after_type is timedelta and datetime.now() - self._created_at > self.remove_after or # The difference from creation time is bigger than remove_after
                rm_after_type is datetime and datetime.now() > self.remove_after) # The current time is larger than remove_after 

    async def initialize(self):
        "Initializes asynchronous elements."
        self.task = asyncio.create_task(self._find_guilds())
    
    async def add_message(self, message: message.BaseMESSAGE):
        """
        Adds a copy of the passed message to each
        guild inside cache.

        Parameters
        -------------
        message: message.BaseMESSAGE
            Message to add.

        Raises
        ---------
        Any
            Any exception raised in :py:meth:`daf.guild.GUILD.add_message`.
        """
        for guild in self.cache.values():
            await guild.add_message(deepcopy(message))

    async def _find_guilds(self):
        """
        Coroutine that finds new guilds from the
        API wrapper.
        """
        dcl = client.get_client()
        while True:
            for dcgld in dcl.guilds:
                if (dcgld not in self.cache and 
                    re.search(self.include_pattern, dcgld.name) is not None and
                    re.search(self.exclude_pattern, dcgld.name) is None
                ):
                    try:
                        new_guild = guild.GUILD(snowflake=dcgld,
                                                messages=deepcopy(self.messages),
                                                logging=self.logging)
                        await new_guild.initialize()
                        self.cache[dcgld] = new_guild
                    except Exception as exc:
                        trace(f"[AutoGUILD:] Unable to add new object.\nReason: {exc}",TraceLEVELS.WARNING)

            await asyncio.sleep(self.interval)

    async def _advertise(self, type_: guild.AdvertiseTaskType):
        """
        Advertises thru all the GUILDs.

        Parameters
        ----------------
        type_: guild.AdvertiseTaskType
            Which task called this method.
            This is just forwarded to GUILDs' _advertise method.
        """
        for g in self.cache.values():
            await g._advertise(type_)

    async def update(self, **kwargs):
        """
        Updates the object with new initialization parameters.

        .. WARNING::
            After calling this method the entire object is reset (this includes it's GUILD objects in cache).
        """
        if "interval" not in kwargs:
            kwargs["interval"] = timedelta(seconds=self.interval)

        return await misc._update(self, **kwargs)

        
