from abc import ABC, abstractmethod
from typing import List

from .constraints import ConstraintBase
from .actions import BaseResponse
from ..events import EventID

import _discord as discord
import asyncio_event_hub as aeh
import re


class ResponderBase(ABC):
    def __init__(
        self,
        keywords: List[str],
        action: BaseResponse,
        constraints: List[ConstraintBase]
    ) -> None:
        self.keywords = list(map(str.lower, keywords))
        self.constraints = constraints
        self.action = action
        self.event_ctrl: aeh.EventController = None

    async def handle_message(self, message: discord.Message):
        "Processes message and performs an action if all constraints satisfied."
        for const in self.constraints:  # Check constraints
            if not const.check(message):
                return
            
        # Check keywords
        for keyword in self.keywords:
            if keyword not in message.content.lower():
                return

        await self.action.perform(message)  # All constraints satisfied

    @abstractmethod
    def initialize(self, event_ctrl: aeh.EventController, client: discord.Client):
        pass

    def close(self):
        self.event_ctrl.remove_listener(EventID.discord_message, self.handle_message)

