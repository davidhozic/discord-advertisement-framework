from datetime import datetime
from typing import Optional, Literal, List, Set, get_args, Iterator

from .tracing import trace
from ..misc import doc, async_util
from ..misc.instance_track import track_id

from .logger_base import C_FILE_NAME_FORBIDDEN_CHAR, C_FILE_MAX_SIZE, LoggerBASE
from .logger_file import LoggerFileBASE

import json
import pathlib
import shutil
import os


__all__ = ("LoggerJSON",)


@track_id
@doc.doc_category("Logging reference", path="logging")
class LoggerJSON(LoggerFileBASE):
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

    EXTENSION = ".json"

    def __init__(
        self,
        path: str = str(pathlib.Path.home().joinpath("daf/History")),
        fallback: Optional[LoggerBASE] = None
    ) -> None:
        super().__init__(path, fallback)

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

    def _get_msg_log_process_file(self, guild, author, after, before, success_rate, guild_type, message_type, logs, filename):
        logs = []
        with open(filename, 'r', encoding="utf-8") as reader:
            data = json.load(reader)

        if guild_type is not None and data["type"] != guild_type or guild is not None and data["id"] != guild:
            return logs

        guild_dict = {"name": data["name"], "id": data["id"], "type": data["type"]}

        for author_ctx in data["message_tracking"].values():
            author_dict = {"name": author_ctx["name"], "id": author_ctx["id"]}
            if author is not None and author_ctx["id"] != author:
                continue

            for message in author_ctx["messages"]:
                if message_type is not None and message["type"] != message_type:
                    continue

                stamp = self._datetime_from_stamp(message["timestamp"])
                if before < stamp or stamp < after:
                    continue

                calc_success_rate = self._calc_success_rate(message)
                if success_rate[0] > calc_success_rate or calc_success_rate > success_rate[1]:
                    continue

                del message["timestamp"]
                message = {"timestamp": stamp, **message}
                message["author"] = author_dict
                message["guild"] = guild_dict
                message["success_rate"] = calc_success_rate
                logs.append(message)

        return logs
    
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
        for filename in self._get_files(".json"):
            with open(filename, 'r', encoding="utf-8") as reader:
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

    def _calc_success_rate(self, message: dict) -> float:
        channel_ctx = message.get("channels")
        if channel_ctx is not None:
            len_s = len(channel_ctx["successful"])
            calc_success_rate = 100.00 * len_s / (len(channel_ctx["failed"]) + len_s)
        else:
            calc_success_rate = 100.00 if message["success_info"]["success"] else 0.0

        return calc_success_rate
