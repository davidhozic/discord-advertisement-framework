from typing import List
from typeguard import typechecked

from .constraints import BaseGuildConstraint
from ..misc.instance_track import track_id
from ..misc.doc import doc_category
from .actions import BaseResponse
from .base import ResponderBase
from ..logic import BaseLogic
from ..events import EventID

import asyncio_event_hub as aeh
import _discord as discord


__all__ = ("GuildResponder",)


@track_id
@doc_category("Auto responder", path="responder")
class GuildResponder(ResponderBase):
    __doc__ = "Guild responder implementation. " + ResponderBase.__doc__

    @typechecked
    def __init__(
        self,
        condition: BaseLogic,
        action: BaseResponse,
        constraints: List[BaseGuildConstraint] = [],
    ) -> None:
        super().__init__(condition, action, constraints)

    async def initialize(self, event_ctrl: aeh.EventController, client: discord.Client):
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
