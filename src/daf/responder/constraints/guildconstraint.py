from typing import Union
from typeguard import typechecked

from .baseconstraint import ConstraintBase

import _discord as discord


class GuildConstraint(ConstraintBase):
    @typechecked
    def __init__(self, guild: Union[int, discord.Guild]) -> None:
        self.guild = guild if isinstance(guild, int) else guild.id

    def check(self, message: discord.Message, client: discord.Client) -> bool:
        if isinstance(message.channel, discord.DMChannel):  # On DM message check if user in same guild
            guild = client.get_guild(self.guild)
            return guild is not None and guild.get_member(message.author.id) is not None

        return message.guild and message.guild.id == self.guild
