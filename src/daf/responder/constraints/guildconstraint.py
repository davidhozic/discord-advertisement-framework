from typing import Union
from typeguard import typechecked

from .baseconstraint import ConstraintBase

import _discord as discord


__all__ = ("BaseGuildConstraint", "GuildConstraint")


class BaseGuildConstraint(ConstraintBase):
    """
    Constraint base for all 
    """

class GuildConstraint(BaseGuildConstraint):
    @typechecked
    def __init__(self, guild: Union[int, discord.Guild]) -> None:
        self.guild = guild if isinstance(guild, int) else guild.id

    def check(self, message: discord.Message, client: discord.Client) -> bool:
        return message.guild and message.guild.id == self.guild
