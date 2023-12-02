"""
This module is responsible for the logging in daf.
It contains all the logging classes.
"""
from datetime import datetime, date
from typing import Optional, Literal, Union, Tuple, List, Any

from .tracing import trace, TraceLEVELS
from ..misc import doc, async_util
from ..misc import write_non_exist
import asyncio

__all__ = (
    "LoggerBASE",
)

# Constants
# ---------------------#
C_FILE_NAME_FORBIDDEN_CHAR = ('<', '>', '"', '/', '\\', '|', '?', '*', ":")
C_FILE_MAX_SIZE = 100000


@doc.doc_category("Logging reference", path="logging")
class LoggerBASE:
    """
    .. versionchanged:: v2.7
        Invite link tracking.

    .. versionadded:: v2.2

    The base class for making loggers.
    This can be used to implement your custom logger as well.
    This does absolutely nothing, and is here just for demonstration.

    Parameters
    ----------------
    fallback: Optional[LoggerBASE]
        The manager to use, in case saving using this manager fails.
    """

    _mutex: asyncio.Lock

    def __init__(self, fallback = None) -> None:
        self.fallback = fallback
        write_non_exist(self, "_mutex", asyncio.Lock())

    async def initialize(self) -> None:
        "Initializes self and the fallback"
        if self.fallback is not None:
            try:
                await self.fallback.initialize()
            except Exception as exc:
                trace(f" Could not initialize {type(self).__name__}'s fallback: {type(self.fallback).__name__}.",
                      TraceLEVELS.WARNING, exc)
                self.fallback = None

    async def _save_log(
        self,
        guild_context: dict,
        message_context: Optional[dict] = None,
        author_context: Optional[dict] = None,
        invite_context: Optional[dict] = None
    ):
        """
        Saves the log of either message attempt or member join into a guild.

        Parameters
        ------------
        guild_context: dict
            Information about the guild.
        message_context: Optional[dict]
            Information about the message sent.
        author_context: Optional[dict]
            Information about the message author (ACCOUNT).
        invite_context: Optional[dict].
            Information about a new guild join by invite.
        """
        raise NotImplementedError

    async def analytic_get_num_messages(
        self,
        guild: Union[int, None] = None,
        author: Union[int, None] = None,
        after: Union[datetime, None] = None,
        before: Union[datetime, None] = None,
        guild_type: Union[Literal["USER", "GUILD"], None] = None,
        message_type: Union[Literal["TextMESSAGE", "VoiceMESSAGE", "DirectMESSAGE"], None] = None,
        sort_by: Literal["successful", "failed", "guild_snow", "guild_name", "author_snow", "author_name"] = "successful",
        sort_by_direction: Literal["asc", "desc"] = "desc",
        limit: int = 500,
        group_by: Literal["year", "month", "day"] = "day"
    ) -> List[Tuple[date, int, int, int, str, int, str]]:
        """
        Counts all the messages in the configured group based on parameters.

        Parameters
        -----------
        guild: int
            The snowflake id of the guild.
        author: int
            The snowflake id of the author.
        after: Union[datetime, None] = None
            Only count messages sent after the datetime.
        before: Union[datetime, None]
            Only count messages sent before the datetime.
        guild_type: Literal["USER", "GUILD"] | None,
            Type of guild.
        message_type: Literal["TextMESSAGE", "VoiceMESSAGE", "DirectMESSAGE"] | None,
            Type of message.
        sort_by: Literal["successful", "failed", "guild_snow", "guild_name", "author_snow", "author_name"],
            Sort items by selected.
            Defaults to "successful"
        sort_by_direction: Literal["asc", "desc"]
            Sort items by ``sort_by`` in selected direction (asc = ascending, desc = descending).
            Defaults to "desc"
        limit: int = 500
            Limit of the rows to return. Defaults to 500.
        group_by: Literal["year", "month", "day"]
            Results returned are grouped by ``group_by``

        Returns
        --------
        list[tuple[date, int, int, int, str, int, str]]
            List of tuples.

            Each tuple contains:

            - Date
            - Successful sends
            - Failed sends
            - Guild snowflake id,
            - Guild name
            - Author snowflake id,
            - Author name
        """
        raise NotImplementedError

    async def analytic_get_message_log(
            self,
            guild: Union[int, None] = None,
            author: Union[int, None] = None,
            after: Union[datetime, None] = None,
            before: Union[datetime, None] = None,
            success_rate: Tuple[float, float] = (0, 100),
            guild_type: Union[Literal["USER", "GUILD"], None] = None,
            message_type: Union[Literal["TextMESSAGE", "VoiceMESSAGE", "DirectMESSAGE"], None] = None,
            sort_by: Literal["timestamp", "success_rate"] = "timestamp",
            sort_by_direction: Literal["asc", "desc"] = "desc",
            limit: int = 500,
    ) -> list:
        raise NotImplementedError

    async def analytic_get_num_invites(
            self,
            guild: Union[int, None] = None,
            after: Union[datetime, None] = None,
            before: Union[datetime, None] = None,
            sort_by: Literal["count", "guild_snow", "guild_name", "invite_id"] = "count",
            sort_by_direction: Literal["asc", "desc"] = "desc",
            limit: int = 500,
            group_by: Literal["year", "month", "day"] = "day"
    ) -> list:
        raise NotImplementedError

    async def analytic_get_invite_log(
        self,
        guild: Union[int, None] = None,
        invite: Union[str, None] = None,
        after: Union[datetime, None] = None,
        before: Union[datetime, None] = None,
        sort_by: Literal["timestamp"] = "timestamp",
        sort_by_direction: Literal["asc", "desc"] = "desc",
        limit: int = 500,
    ) -> list:
        raise NotImplementedError

    async def delete_logs(self, table: Any, logs: List[Any]):
        """
        Method used to delete log objects objects.

        Parameters
        ------------
        table: Any
            The logging table to delete from.
        primary_keys: List[int]
            List of Primary Key IDs that match the rows of the table to delete.
        """
        raise NotImplementedError

    @async_util.with_semaphore("_mutex")
    async def update(self, **kwargs):
        """
        Used to update the original parameters.

        Parameters
        -------------
        kwargs: Any
            Keyword arguments of any original parameters.

        Raises
        ----------
        TypeError
            Invalid keyword argument was passed.
        Other
            Other exceptions raised from ``.initialize`` method (if it exists).
        """
        await async_util.update_obj_param(self, **kwargs)

