from typing import Union
from typeguard import typechecked

from .baseconstraint import ConstraintBase
from ...misc.doc import doc_category

import _discord as discord


__all__ = ("BaseGuildConstraint", "GuildConstraint")


@doc_category("Auto responder")
class BaseGuildConstraint(ConstraintBase):
    """
    Constraint base for all guild constraints.
    """

@doc_category("Auto responder")
class GuildConstraint(BaseGuildConstraint):
    """
    Constraint that checks if the message originated
    from the specific ``guild``.

    Parameters
    ----------------
    guild: int | discord.Guild
        The guild to which the message must be sent for the constraint to be fulfilled.
    """
    @typechecked
    def __init__(self, guild: Union[int, discord.Guild]) -> None:
        self.guild = guild if isinstance(guild, int) else guild.id

    def check(self, message: discord.Message, client: discord.Client) -> bool:
        return message.guild and message.guild.id == self.guild
