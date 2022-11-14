"""
This module contains definitions related
to automatic generation of objects.
"""

from typing import Optional, Union, List, Dict
from datetime import datetime, timedelta
from typeguard import typechecked

from .logging.tracing import TraceLEVELS, trace

from . import misc
from . import guild
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

    TODO: Implement update method
    TODO: Implement add_message method that will add messages to guilds based on AutoCHANNEL.

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
        "logging",
        "interval",
        "cache",
        "task",
        "_created_at"
    )

    @typechecked
    def __init__(self,
                 include_pattern: str,
                 exclude_pattern: Optional[str] = None,
                 remove_after: Optional[Union[timedelta, datetime]] = None,
                 logging: Optional[bool] = False,
                 interval: Optional[timedelta] = GUILD_GEN_REFRESH_INT) -> None:
        self.include_pattern = include_pattern
        self.exclude_pattern = exclude_pattern
        self.remove_after = remove_after  # TODO: Implement auto removal
        self.logging = logging
        self.interval = interval.total_seconds() # In seconds
        self.cache: Dict[guild.GUILD] = {}
        self.task = None # Holds the Task object of _find_guilds that needs to be cleaned upon garbage collection.
        self._created_at = datetime.now()

    def __del__(self):
        "Called when garbage collected, cleans all the tasks"
        self.task.cancel()

    @property
    def guilds(self) -> List[guild.GUILD]:
        "Returns cached found GUILD objects."
        return self.cache.copy()

    @property
    def created_at(self) -> datetime:
        """
        Returns the datetime of when the object has been created.
        """
        return self._created_at

    def _check_state(self) -> bool:
        """
        Checks if the object is ready to be deleted.

        Returns
        ----------
        True
            The object should be deleted.
        False
            The object is in proper state, do not delete.
        """
        rm_after_type = type(self.remove_after)
        return (rm_after_type is timedelta and datetime.now() - self._created_at > self.remove_after or # The difference from creation time is bigger than remove_after
                rm_after_type is datetime and datetime.now() > self.remove_after) # The current time is larger than remove_after 

    async def initialize(self):
        "Initializes asynchronous elements."
        self.task = asyncio.create_task(self._find_guilds())

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
                        new_guild = guild.GUILD(snowflake=dcgld, logging=self.logging)
                        await new_guild.initialize()
                        self.cache[dcgld] = new_guild
                    except Exception as exc:
                        trace(f"[AutoGUILD:] Unable to add new object.\nReason: {exc}", TraceLEVELS.WARNING)

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
        
