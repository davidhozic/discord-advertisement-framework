from typing import Union
from typeguard import typechecked

from .baseconstraint import ConstraintBase

import _discord as discord


class GuildConstraint(ConstraintBase):
    @typechecked
    def __init__(self, guild: Union[int, discord.Guild]) -> None:
        self.guild = guild if isinstance(guild, int) else guild.id

    def check(self, message: discord.Message) -> bool:
        return message.guild and message.guild.id == self.guild

