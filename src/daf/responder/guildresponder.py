from typing import List
from typeguard import typechecked

from .base import ResponderBase
from .logic import *
from .constraints import BaseGuildConstraint
from .actions import BaseResponse
from ..events import EventID

import asyncio_event_hub as aeh
import _discord as discord


class GuildResponder(ResponderBase):
    @typechecked
    def __init__(
        self,
        condition: BaseLogic,
        action: BaseResponse,
        constraints: List[BaseGuildConstraint] = [],
    ) -> None:
        super().__init__(condition, action, constraints)

    def initialize(self, event_ctrl: aeh.EventController, client: discord.Client):
        event_ctrl.add_listener(
            EventID.discord_message,
            self.handle_message,
            lambda m:
                isinstance(m.channel, discord.TextChannel) and
                (member := m.guild.get_member(client.user.id)) and
                not member.pending and
                m.channel.permissions_for(member).send_messages
        )
        self.event_ctrl = event_ctrl
        self.client = client
