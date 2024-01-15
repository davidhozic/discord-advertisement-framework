from typing import List
from typeguard import typechecked

from .base import ResponderBase
from .logic import *
from .constraints import BaseDMConstraint
from .actions import DMResponse
from ..events import EventID

import asyncio_event_hub as aeh
import _discord as discord


class DMResponder(ResponderBase):
    @typechecked
    def __init__(
        self,
        condition: BaseLogic,    
        action: DMResponse,
        constraints: List[BaseDMConstraint] = [], 
    ) -> None:
        super().__init__(condition, action, constraints)

    def initialize(self, event_ctrl: aeh.EventController, client: discord.Client):
        event_ctrl.add_listener(
            EventID.discord_message,
            self.handle_message,
            lambda m: isinstance(m.channel, discord.DMChannel)
        )
        self.event_ctrl = event_ctrl
        self.client = client
