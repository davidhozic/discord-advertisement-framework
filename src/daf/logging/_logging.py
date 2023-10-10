"""
This module is responsible for the logging in daf.
It contains all the logging classes.
"""
from datetime import datetime, date
from typing import Optional, Literal, Union, Tuple, List, Any, Set, get_args 

from .tracing import trace, TraceLEVELS
from ..misc import doc, async_util
from ..misc import write_non_exist
from ..misc.instance_track import track_id


import json
import csv
import pathlib
import shutil
import os
import asyncio
import time

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


@track_id
@doc.doc_category("Logging reference", path="logging")
class LoggerJSON(LoggerBASE):
    """
    .. versionchanged:: v3.1
        The index of each log is now a snowflake ID.
        It consists of <timestamp in ms since epoch> | <sequence number>.
        <sequence number> is of fixed size 8 bits, while timestamp is not of fixed size.

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
        self._sequence_number = 0
        super().__init__(fallback)

    def initialize(self):
        trace(f"{type(self).__name__} logs will be saved to {self.path}")
        return super().initialize()

    def _generate_snowflake(self) -> int:
        """
        Generates an unique snowflake index (id) for identifying logs.
        The returned number is not fixed size and it consists of
        <sequence number> | <timestamp in ms since epoch>.
        <sequence number> is of fixed size 8 bits.
        """
        stamp = int(time.time() * 1000)
        seq = self._sequence_number
        snowflake = (
            seq |
            (stamp << 8)
        )

        self._sequence_number = (seq + 1) % 0xFF  # modules by max value of 8 bits
        return snowflake

    @async_util.with_semaphore("_mutex")
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
                    "index": self._generate_snowflake(),
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
                    "member": {**invite_context["member"]},
                    "index": self._generate_snowflake(),
                    "timestamp": timestamp}
                )

            json.dump(json_data, f_writer, indent=4, ensure_ascii=False)
            f_writer.truncate()  # Remove any old data

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
        limit: Optional[int] = 500
    ):
        if after is None:
            after = datetime.min

        if before is None:
            before = datetime.max

        logs = []
        for path, dirs, files in os.walk(self.path):
            for filename in files:
                if not filename.endswith(".json"):
                    continue

                with open(os.path.join(path, filename), 'r', encoding="utf-8") as reader:
                    data = json.load(reader)

                if guild_type is not None and data["type"] != guild_type:
                    continue

                if guild is not None and data["id"] != guild:
                    continue

                guild_dict = {"name": data["name"], "id": data["id"], "type": data["type"]}

                for author_ctx in data["message_tracking"].values():
                    author_dict = {"name": author_ctx["name"], "id": author_ctx["id"]}
                    if author is not None and author_ctx["id"] != author:
                        continue

                    for message in author_ctx["messages"]:
                        if message_type is not None and message["type"] != message_type:
                            continue

                        message["author"] = author_dict
                        message["guild"] = guild_dict

                        stamp = self._datetime_from_stamp(message["timestamp"])
                        if stamp < after or stamp > before:
                            continue

                        del message["timestamp"]
                        message = {"timestamp": stamp, **message}
                        calc_success_rate = self._calc_success_rate(message)

                        if calc_success_rate < success_rate[0] or calc_success_rate > success_rate[1]:
                            continue

                        message["success_rate"] = calc_success_rate
                        logs.append(message)

        sorted_ = sorted(logs, key=lambda log: log[sort_by], reverse=sort_by_direction == "desc")
        if limit is not None:
            sorted_ = sorted_[:limit]

        return sorted_

    def _calc_success_rate(self, message: dict) -> float:
        channel_ctx = message.get("channels")
        if channel_ctx is not None:
            len_s = len(channel_ctx["successful"])
            calc_success_rate = 100.00 * len_s / (len(channel_ctx["failed"]) + len_s)
        else:
            calc_success_rate = 100.00 if message["success_info"]["success"] else 0.0
        return calc_success_rate

    async def analytic_get_num_messages(
        self,
        guild: Union[int, None] = None,
        author: Union[int, None] = None,
        after: datetime = datetime.min,
        before: datetime = datetime.max,
        guild_type: Union[Literal["USER", "GUILD"], None] = None,
        message_type: Union[Literal["TextMESSAGE", "VoiceMESSAGE", "DirectMESSAGE"], None] = None,
        sort_by: Literal["successful", "failed", "guild_snow", "guild_name", "author_snow", "author_name"] = "successful",
        sort_by_direction: Literal["asc", "desc"] = "desc",
        limit: int = 500,
        group_by: Literal["year", "month", "day"] = "day"
    ) -> list:
        logs = await self.analytic_get_message_log(
            guild,
            author,
            after,
            before,
            guild_type=guild_type,
            message_type=message_type,
            limit=None
        )
        cuts = {}
        if not len(logs):
            return []

        regions = ["day", "month", "year"]
        regions_left = list(reversed(regions[regions.index(group_by):]))

        sort_by_values = get_args(LoggerJSON.analytic_get_num_messages.__annotations__["sort_by"])

        def get_region_text(stamp):
            return '-'.join(f"{getattr(stamp, region):02d}" for region in regions_left)

        for log in logs:
            time_group = get_region_text(log["timestamp"])
            guild = log["guild"]
            author = log["author"]
            group_value = time_group, guild["id"], author["id"]
            if group_value not in cuts:
                cut_group = cuts[group_value] = [
                    time_group,
                    0,
                    0,
                    guild["id"],
                    guild["name"],
                    author["id"],
                    author["name"]
                ]
            else:
                cut_group = cuts[group_value]

            if log["success_rate"] == 100:
                cut_group[1] += 1
            else:
                cut_group[2] += 1

        # key: first index is timestamp group, so offset by one and then calculate index by annotation position
        return sorted(
            cuts.values(),
            key=lambda row: row[sort_by_values.index(sort_by) + 1],
            reverse=sort_by_direction == "desc"
        )[:limit]
    
    async def analytic_get_invite_log(
        self,
        guild: Optional[int] = None,
        invite: Optional[str] = None,
        after: Optional[datetime] = None,
        before: Optional[datetime] = None,
        sort_by: Literal['timestamp'] = "timestamp",
        sort_by_direction: Literal['asc', 'desc'] = "desc",
        limit: Optional[int] = 50
    ) -> list:
        if after is None:
            after = datetime.min

        if before is None:
            before = datetime.max

        logs = []
        for path, dirs, files in os.walk(self.path):
            for filename in files:
                if not filename.endswith(".json"):
                    continue

                with open(os.path.join(path, filename), 'r', encoding="utf-8") as reader:
                    data = json.load(reader)

                if guild is not None and data["id"] != guild:
                    continue

                guild_dict = {"name": data["name"], "id": data["id"], "type": data["type"]}

                for invite_id, invite_logs in data["invite_tracking"].items():
                    if invite is not None and invite_id != invite:
                        continue

                    for log in invite_logs:
                        log["guild"] = guild_dict
                        log["invite"] = f"https://discord.gg/{invite_id}"

                        stamp = self._datetime_from_stamp(log["timestamp"])
                        if stamp < after or stamp > before:
                            continue

                        del log["timestamp"]
                        log = {"timestamp": stamp, **log}
                        logs.append(log)
        
        sorted_ = sorted(logs, key=lambda log: log[sort_by], reverse=sort_by_direction == "desc")
        if limit is not None:
            sorted_ = sorted_[:limit]

        return sorted_

    async def analytic_get_num_invites(
        self,
        guild: Optional[int] = None,
        after: Optional[datetime] = None,
        before: Optional[datetime] = None,
        sort_by: Literal['count', 'guild_snow', 'guild_name', 'invite_id'] = "count",
        sort_by_direction: Literal['asc', 'desc'] = "desc",
        limit: int = 500,
        group_by: Literal['year', 'month', 'day'] = "day"
    ) -> list:
        logs = await self.analytic_get_invite_log(
            guild,
            after,
            before,
            limit=None
        )
        cuts = {}
        if not len(logs):
            return []

        regions = ["day", "month", "year"]
        regions_left = list(reversed(regions[regions.index(group_by):]))

        sort_by_values = get_args(LoggerJSON.analytic_get_num_invites.__annotations__["sort_by"])

        def get_region_text(stamp):
            return '-'.join(f"{getattr(stamp, region):02d}" for region in regions_left)

        for log in logs:
            time_group = get_region_text(log["timestamp"])
            guild = log["guild"]
            invite = log["invite"]
            group_value = time_group, guild["id"], invite
            if group_value not in cuts:
                cut_group = cuts[group_value] = [
                    time_group,
                    0,
                    guild["id"],
                    guild["name"],
                    invite
                ]
            else:
                cut_group = cuts[group_value]

            cut_group[1] += 1

        # key: first index is timestamp group, so offset by one and then calculate index by annotation position
        return sorted(
            cuts.values(),
            key=lambda row: row[sort_by_values.index(sort_by) + 1],
            reverse=sort_by_direction == "desc"
        )[:limit]

    @async_util.with_semaphore("_mutex")
    async def delete_logs(self, logs: List[dict]):
        if "type" in logs[0]:  # Message log
            filterer = self._remove_message_logs
        else:  # Invite log
            filterer = self._remove_invite_logs

        indexes = set(x["index"] for x in logs)
        for path, dirs, files in os.walk(self.path):
            for filename in files:
                if filename.endswith(".json"):
                    with open(os.path.join(path, filename), 'r+', encoding="utf-8") as f_log:
                        data = json.load(f_log)
                        filterer(data, indexes)
                        f_log.seek(0)
                        f_log.truncate()
                        json.dump(data, f_log, indent=4)

    def _datetime_from_stamp(self, timestamp: str):
        date_, time_ = timestamp.split(' ')
        day, month, year = map(int, date_.split('.'))
        hour, minute, second = map(int, time_.split(':'))
        stamp = datetime(year, month, day, hour, minute, second)
        return stamp

    def _remove_message_logs(self, data: dict, indexes: Set[int]):
        for author_ctx in data["message_tracking"].values():
            for message in author_ctx["messages"].copy():
                if message["index"] not in indexes:
                    continue

                author_ctx["messages"].remove(message)

    def _remove_invite_logs(self, data: dict, indexes: Set[int]):
        for logs in data["invite_tracking"].values():
            for log in logs.copy():
                if log["index"] not in indexes:
                    continue

                logs.remove(log)


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
