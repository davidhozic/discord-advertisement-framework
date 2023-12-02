"""
Implements common functionality of file-based loggers.
"""
from typing import Union, Tuple, Literal, Optional, Iterator, get_args
from pathlib import Path
from time import time
from datetime import datetime

from .logger_base import LoggerBASE
from ..logging.tracing import trace

import os


class LoggerFileBASE(LoggerBASE):
    EXTENSION = NotImplemented

    def __init__(
        self,
        path: str = str(Path.home().joinpath("daf/History")),
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
        stamp = int(time() * 1000)
        seq = self._sequence_number
        snowflake = (
            seq |
            (stamp << 8)
        )

        self._sequence_number = (seq + 1) % 0xFF  # modules by max value of 8 bits
        return snowflake

    def _get_files(self, filetype: str) -> Iterator[str]:
        for path, dirs, files in os.walk(self.path):
            for filename in files:
                if filename.endswith(filetype):
                    yield os.path.join(path, filename)

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
        for filename in self._get_files(self.EXTENSION):
            logs.extend(
                self._get_msg_log_process_file(
                    guild,
                    author,
                    after,
                    before,
                    success_rate,
                    guild_type,
                    message_type,
                    logs,
                    filename
                )
            )

        sorted_ = sorted(logs, key=lambda log: log[sort_by], reverse=sort_by_direction == "desc")
        if limit is not None:
            sorted_ = sorted_[:limit]

        return sorted_

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

        sort_by_values = get_args(LoggerFileBASE.analytic_get_num_messages.__annotations__["sort_by"])

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

    def _get_msg_log_process_file(self):
        raise NotImplementedError
