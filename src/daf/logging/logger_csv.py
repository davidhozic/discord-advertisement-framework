from datetime import datetime, date
from typing import Optional, List, Any

from .tracing import trace
from ..misc import doc
from ..misc.instance_track import track_id

from .logger_base import LoggerBASE, C_FILE_NAME_FORBIDDEN_CHAR
from .logger_file import LoggerFileBASE

import json
import csv
import pathlib
import os


__all__ = ("LoggerCSV",)


@track_id
@doc.doc_category("Logging reference", path="logging")
class LoggerCSV(LoggerFileBASE):
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
    EXTENSION = ".csv"

    def __init__(
        self,
        path: str = str(pathlib.Path.home().joinpath("daf/History")),
        delimiter: str = ';',
        fallback: Optional[LoggerBASE] = None
    ) -> None:
        self.delimiter = delimiter
        super().__init__(path, fallback)

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

                if channels_str:
                    channels_str = json.dumps(channels_str, ensure_ascii=False)

                if success_info_str:
                    success_info_str = json.dumps(success_info_str, ensure_ascii=False)

                csv_writer.writerow([
                    self._generate_snowflake(),
                    timestamp, guild_context["type"], guild_context["name"], guild_context["id"],
                    *list(author_context.values()),
                    message_context["type"], json.dumps(message_context["sent_data"], ensure_ascii=False),
                    message_context.get("mode", ""), channels_str, success_info_str
                ])

            except Exception as exc:
                raise OSError(*exc.args) from exc  # Raise OSError for any type of exceptions

    def _get_msg_log_process_file(
        self,
        guild,
        author,
        after,
        before,
        success_rate,
        guild_type,
        message_type,
        logs,
        filename
    ):
        logs = []
        with open(filename, encoding="utf-8") as file:
            for (
                index, stamp, guild_type_r, guild_name, guild_id, author_name, author_id, message_type_r,
                sent_data, send_mode, channels, dm_success
            ) in csv.reader(file, delimiter=self.delimiter):

                if guild_type is not None and guild_type != guild_type_r:
                    continue

                if message_type is not None and message_type != message_type_r:
                    continue

                # Convert string date and time to datetime object
                date, time_d = stamp.split(' ')
                date = date.split('.')
                time_d = time_d.split(':')
                stamp = datetime(*map(int, reversed(date)), *map(int, time_d))

                if stamp > before or stamp < after:
                    continue

                # Convert string IDs to int
                guild_id = int(guild_id)
                if guild is not None and guild != guild_id:
                    continue

                author_id = int(author_id)
                if author is not None and author != author_id:
                    continue

                # Convert JSON fields to dict
                sent_data = json.loads(sent_data)
                channels = json.loads(channels) if channels else None
                dm_success = json.loads(dm_success) if dm_success else None
                
                # Make structures
                guild_ctx = {"type": guild_type_r, "name": guild_name, "id": guild_id}
                author_ctx = {"name": author_name, "id": author_id}

                if dm_success is not None:
                    calc_success_rate = 0.0 if not dm_success["success"] else 1.0
                else:
                    calc_success_rate = (
                        100.0 * len(channels["successful"]) /
                        (len(channels["successful"]) + len(channels["failed"]))
                    )

                if calc_success_rate < success_rate[0] or calc_success_rate > success_rate[1]: 
                    continue

                logs.append({
                    "index": index,
                    "timestamp": stamp,
                    "sent_data": sent_data,
                    "channels": channels,
                    "type": message_type_r,
                    "mode": send_mode,
                    "author": author_ctx,
                    "guild": guild_ctx,
                    "success_rate": calc_success_rate
                })

        return logs