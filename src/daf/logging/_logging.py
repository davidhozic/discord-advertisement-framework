"""
This module is responsible for the logging in daf.
It contains all the logging classes.
"""
from datetime import datetime, date
from typing import Optional, Literal, Union, Tuple, List

from .tracing import trace, TraceLEVELS
from ..misc import doc, async_util


import json
import csv
import pathlib
import shutil

__all__ = (
    "LoggerBASE",
    "LoggerJSON",
    "LoggerCSV",
    "get_logger",
    "save_log"
)

# Constants
# ---------------------#
C_FILE_NAME_FORBIDDEN_CHAR = ('<', '>', '"', '/', '\\', '|', '?', '*', ":")
C_FILE_MAX_SIZE = 100000


class GLOBAL:
    "Singleton for global variables"
    logger = None


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
    def __init__(self, fallback = None) -> None:
        self.fallback = fallback

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


@doc.doc_category("Logging reference", path="logging")
class LoggerCSV(LoggerBASE):
    """
    .. versionadded:: v2.2

    .. caution::

        Invite link tracking is not supported with LoggerCSV!

    Logging class for generating .csv file logs.
    The logs are saved into CSV files and fragmented
    by guild/user and day (each day, new file for each guild).

    Each entry is in the following format:

    ``Timestamp, Guild Type, Guild Name, Guild Snowflake, Message Type,
    Sent Data, Message Mode (Optional), Channels (Optional), Success Info (Optional)``

    Parameters
    ----------------
    path: str
        Path to the folder where logs will be saved. Defaults to /<user-home>/daf/History
    delimiter: str
        The delimiter between columns to use. Defaults to ';'
    fallback: Optional[LoggerBASE]
        The manager to use, in case saving using this manager fails.

    Raises
    ----------
    OSError
        Something went wrong at OS level (insufficient permissions?)
        and fallback failed as well.
    """
    def __init__(
        self,
        path: str = str(pathlib.Path.home().joinpath("daf/History")),
        delimiter: str = ';',
        fallback: Optional[LoggerBASE] = None
    ) -> None:
        self.path = path
        self.delimiter = delimiter
        super().__init__(fallback)
    
    def initialize(self):
        trace(f"{type(self).__name__} logs will be saved to {self.path}")
        return super().initialize()

    async def _save_log(
            self,
            guild_context: dict,
            message_context: Optional[dict] = None,
            author_context: Optional[dict] = None,
            invite_context: Optional[dict] = None
    ):
        if invite_context is not None:  # Not implemented on CSV
            raise NotImplementedError("Invite tracking not available when using LoggerCSV")

        timestruct = datetime.now()
        timestamp = "{:02d}.{:02d}.{:04d} {:02d}:{:02d}:{:02d}".format(timestruct.day, timestruct.month, timestruct.year,
                                                                    timestruct.hour, timestruct.minute, timestruct.second)

        logging_output = (pathlib.Path(self.path)
                        .joinpath("{:02d}".format(timestruct.year))
                        .joinpath("{:02d}".format(timestruct.month))
                        .joinpath("{:02d}".format(timestruct.day)))

        logging_output.mkdir(parents=True, exist_ok=True)
        logging_output = logging_output.joinpath("".join(char if char not in C_FILE_NAME_FORBIDDEN_CHAR
                                                              else "#" for char in guild_context["name"]) + ".csv")          
        # Create file if it doesn't exist
        if not logging_output.exists():
            logging_output.touch()

        # Write to file
        with open(logging_output, 'a', encoding='utf-8', newline='') as f_writer:
            try:
                csv_writer = csv.writer(f_writer, delimiter=self.delimiter, quoting=csv.QUOTE_NONNUMERIC, quotechar='"')
                # Timestamp, Guild Type, Guild Name, Guild Snowflake, Author Name, Author Snowflake
                # Message Type, Sent Data, Message Mode, Message Channels, Success Info
                channels_str = message_context.get("channels", "")
                success_info_str = message_context.get("success_info", "")

                if channels_str != "":
                    channels_str = json.dumps(channels_str, ensure_ascii=False)

                if success_info_str != "":
                    success_info_str = json.dumps(success_info_str, ensure_ascii=False)

                csv_writer.writerow([
                    timestamp, guild_context["type"], guild_context["name"], guild_context["id"],
                    *list(author_context.values()),
                    message_context["type"], json.dumps(message_context["sent_data"], ensure_ascii=False),
                    message_context.get("mode", ""), channels_str, success_info_str
                ])

            except Exception as exc:
                raise OSError(*exc.args) from exc  # Raise OSError for any type of exceptions


@doc.doc_category("Logging reference", path="logging")
class LoggerJSON(LoggerBASE):
    """
    .. versionchanged:: v2.8
        When file reaches size of 100 kilobytes, a new file is created.

    .. versionadded:: v2.2

    Logging class for generating .json file logs.
    The logs are saved into JSON files and fragmented
    by guild/user and day (each day, new file for each guild).

    Parameters
    ----------------
    path: Optional[str]
        Path to the folder where logs will be saved. Defaults to /<user-home>/daf/History
    fallback: Optional[LoggerBASE]
        The manager to use, in case saving using this manager fails.

    Raises
    ----------
    OSError
        Something went wrong at OS level (insufficient permissions?)
        and fallback failed as well.
    """
    def __init__(
        self,
        path: str = str(pathlib.Path.home().joinpath("daf/History")),
        fallback: Optional[LoggerBASE] = None
    ) -> None:
        self.path = path
        super().__init__(fallback)

    def initialize(self):
        trace(f"{type(self).__name__} logs will be saved to {self.path}")
        return super().initialize()

    async def _save_log(
        self,
        guild_context: dict,
        message_context: Optional[dict] = None,
        author_context: Optional[dict] = None,
        invite_context: Optional[dict] = None
    ):
        def replace_strings(name: str):
            return "".join(
                char
                if char not in C_FILE_NAME_FORBIDDEN_CHAR
                else "#" for char in name
            )

        timestruct = datetime.now()
        timestamp = "{:02d}.{:02d}.{:04d} {:02d}:{:02d}:{:02d}".format(timestruct.day, timestruct.month, timestruct.year,
                                                                    timestruct.hour, timestruct.minute, timestruct.second)

        logging_output = (pathlib.Path(self.path)
                        .joinpath("{:02d}".format(timestruct.year))
                        .joinpath("{:02d}".format(timestruct.month))
                        .joinpath("{:02d}".format(timestruct.day)))

        logging_output.mkdir(parents=True, exist_ok=True)
        logging_output = logging_output.joinpath(replace_strings(guild_context["name"]) + ".json")
        # Create file if it doesn't exist
        file_exists = True
        if not logging_output.exists():
            logging_output.touch()
            file_exists = False

        # Performance issues
        elif logging_output.stat().st_size > C_FILE_MAX_SIZE:
            logging_dir = logging_output.parent
            logging_filename = logging_output.name.replace(".json", "")
            new_index = str(len(list(logging_dir.glob(f"{logging_filename}*"))))
            logging_output.rename(
                logging_dir.joinpath(logging_filename + new_index + ".json")
            )
            file_exists = False
            logging_output.touch()

        # Write to file
        with open(logging_output, 'r+', encoding='utf-8') as f_writer:
            json_data = None
            if file_exists:
                try:
                    json_data: dict = json.load(f_writer)
                except json.JSONDecodeError:
                    # No valid json in the file, create a .old file to store this invalid data.
                    # Copy-paste to .old file to prevent data loss
                    shutil.copyfile(logging_output, f"{logging_output}.old")
                finally:
                    f_writer.seek(0)  # Reset cursor to the beginning of the file after reading

            if json_data is None:
                # Some error or new file
                json_data = {}
                json_data["name"] = guild_context["name"]
                json_data["id"] = guild_context["id"]
                json_data["type"] = guild_context["type"]
                json_data["invite_tracking"] = {}
                json_data["message_tracking"] = {}

            # Message logs
            if message_context is not None:
                json_data_messages = json_data["message_tracking"]
                author_id_str = str(author_context["id"])
                if author_id_str not in json_data_messages:
                    messages = author_context["messages"] = []
                    json_data_messages[author_id_str] = author_context
                else:
                    messages = json_data_messages[author_id_str]["messages"]

                messages.insert(0, {
                    **message_context,
                    "index": messages[0]["index"] + 1 if len(messages) else 0,
                    "timestamp": timestamp}
                )

            # Invite link tracking
            if invite_context is not None:
                json_data_invites = json_data["invite_tracking"]
                invite_id = invite_context["id"]
                if invite_id not in json_data_invites:
                    json_data_invites[invite_id] = []

                invite_list: list = json_data_invites[invite_id]
                invite_list.insert(0, {
                    **invite_context["member"],
                    "index": invite_list[0]["index"] + 1 if len(invite_list) else 0,
                    "timestamp": timestamp}
                )

            json.dump(json_data, f_writer, indent=4, ensure_ascii=False)
            f_writer.truncate()  # Remove any old data


async def initialize(logger: LoggerBASE) -> None:
    """
    Initialization coroutine for the module.

    Parameters
    --------------
    The logger manager to use for saving logs.
    """
    while logger is not None:
        try:
            await logger.initialize()
            break
        except Exception as exc:
            trace(f"Could not initialize manager {type(logger).__name__}, falling to {type(logger.fallback).__name__}",
            TraceLEVELS.WARNING, exc)
            logger = logger.fallback # Could not initialize, try fallback
    else:
        trace("Logging will be disabled as the logging manager and it's fallbacks all failed initialization",
              TraceLEVELS.ERROR)

    GLOBAL.logger = logger


@doc.doc_category("Logging reference", path="logging")
def get_logger() -> LoggerBASE:
    """
    Returns
    ---------
    LoggerBASE
        The selected logging object which is of inherited type from LoggerBASE.
    """
    return GLOBAL.logger


def _set_logger(logger: LoggerBASE):
    """
    Set's the logger to something new.

    Parameters
    -------------
    logger: LoggerBASE
        The logger to use.
    """
    GLOBAL.logger = logger


async def save_log(
        guild_context: dict,
        message_context: Optional[dict] = None,
        author_context: Optional[dict] = None,
        invite_context: Optional[dict] = None
):
    """
    Saves the log to the selected manager or saves
    to the fallback manager if logging fails to the selected.

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
    mgr: LoggerBASE = GLOBAL.logger

    # Don't spam the console if no loggers are available
    if mgr is None:
        return

    while mgr is not None:
        try:
            await mgr._save_log(guild_context, message_context, author_context, invite_context)
            break
        except Exception as exc:
            trace(
                f"{type(mgr).__name__} failed, falling to {type(mgr.fallback).__name__}",
                TraceLEVELS.WARNING,
                exc
            )
            mgr = mgr.fallback  # Could not initialize, try fallback
    else:
        trace("Could not save log to the manager or any of it's fallback", TraceLEVELS.ERROR)
