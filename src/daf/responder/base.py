
from abc import ABC, abstractmethod
from typing import List

from .constraints import ConstraintBase
from .actions import BaseResponse
from ..logic import BaseLogic
from ..events import EventID

import asyncio_event_hub as aeh
import _discord as discord


__all__ = ("ResponderBase",)


class ResponderBase(ABC):
    """
    The responder is an object capable of making automatic replies to messages based on some
    keyword condition and constraints.

    Parameters
    --------------
    condition: BaseLogic
        The match condition. The condition represents the
        match condition of message's text.
    action: BaseResponse
        Represents the action taken on both ``condition`` and ``constraints`` being fulfilled.
    constraints: list[ConstraintBase]
        In addition to ``condition``, constraints add additional checks that need to be fulfilled
        before performing an action.
        All of the constraints inside the ``constraints`` list need to be fulfilled.
    """
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
        if not self.condition.check(message.clean_content.lower()):
            return

        await self.action.perform(message)  # All constraints satisfied

    @abstractmethod
    async def initialize(self, event_ctrl: aeh.EventController, client: discord.Client):
        pass

    def close(self):
        self.event_ctrl.remove_listener(EventID.discord_message, self.handle_message)
