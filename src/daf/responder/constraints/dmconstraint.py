from typing import Union
from typeguard import typechecked

from .baseconstraint import ConstraintBase

import _discord as discord


__all__ = ("BaseDMConstraint", "MemberOfGuildConstraint")


class BaseDMConstraint(ConstraintBase):
    """
    Base for constraints that are DM specific.
    """


class MemberOfGuildConstraint(BaseDMConstraint):
    """
    Constraint that checks if the DM message author
    is part of the ``guild``.

    Parameters
    ----------------
    guild: int | discord.Guild

    """
    @typechecked
    def __init__(self, guild: Union[int, discord.Guild]) -> None:
        self.guild = guild if isinstance(guild, int) else guild.id

    def check(self, message: discord.Message, client: discord.Client) -> bool:
        guild = client.get_guild(self.guild)
        return guild is not None and guild.get_member(message.author.id) is not None
