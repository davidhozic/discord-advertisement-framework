from typeguard import typechecked
from typing import List

from ..misc.instance_track import track_id
from .constraints import BaseDMConstraint
from ..misc.doc import doc_category
from .actions import DMResponse
from .base import ResponderBase
from ..logic import BaseLogic
from ..events import EventID

import asyncio_event_hub as aeh
import _discord as discord


__all__ = ("DMResponder",)


@track_id
@doc_category("Auto responder", path="responder")
class DMResponder(ResponderBase):
    __doc__ = "DM responder implementation. " + ResponderBase.__doc__

    @typechecked
    def __init__(
        self,
        condition: BaseLogic,    
        action: DMResponse,
        constraints: List[BaseDMConstraint] = [], 
    ) -> None:
        super().__init__(condition, action, constraints)

    async def initialize(self, event_ctrl: aeh.EventController, client: discord.Client):
        event_ctrl.add_listener(
            EventID.discord_message,
            self.handle_message,
            lambda m: isinstance(m.channel, discord.DMChannel)
        )
        self.event_ctrl = event_ctrl
        self.client = client
