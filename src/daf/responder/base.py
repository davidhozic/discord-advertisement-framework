from abc import ABC, abstractmethod
from typing import List

from .constraints import ConstraintBase
from .logic import BaseLogic
from .actions import BaseResponse
from ..events import EventID

import _discord as discord
import asyncio_event_hub as aeh


__all__ = ("ResponderBase",)


class ResponderBase(ABC):
    def __init__(
        self,
        condition: BaseLogic,
        action: BaseResponse,
        constraints: List[ConstraintBase]
    ) -> None:
        self.condition = condition
        self.constraints = constraints
        self.action = action
        self.event_ctrl: aeh.EventController = None
        self.client: discord.Client = None

    async def handle_message(self, message: discord.Message):
        "Processes message and performs an action if all constraints satisfied."
        for const in self.constraints:  # Check constraints
            if not const.check(message, self.client):
                return

        # Check keywords
        if not self.condition.check(message.content):
            return

        await self.action.perform(message)  # All constraints satisfied

    @abstractmethod
    def initialize(self, event_ctrl: aeh.EventController, client: discord.Client):
        pass

    def close(self):
        self.event_ctrl.remove_listener(EventID.discord_message, self.handle_message)

