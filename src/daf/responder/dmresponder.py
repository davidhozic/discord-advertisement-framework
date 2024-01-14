from typing import List
from typeguard import typechecked

from .base import ResponderBase
from .constraints import ConstraintBase
from .actions import DMResponse
from ..events import EventID

import asyncio_event_hub as aeh
import _discord as discord


class DMResponder(ResponderBase):
    @typechecked
    def __init__(
        self,
        keywords: List[str],    
        action: DMResponse,
        constraints: List[ConstraintBase] = [], 
    ) -> None:
        super().__init__(keywords, action, constraints)

    def initialize(self, event_ctrl: aeh.EventController, client: discord.Client):
        event_ctrl.add_listener(
            EventID.discord_message,
            self.handle_message,
            lambda m: isinstance(m.channel, discord.DMChannel)
        )
        self.event_ctrl = event_ctrl
        self.client = client
