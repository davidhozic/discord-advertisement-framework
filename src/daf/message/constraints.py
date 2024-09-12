"""
Implements additional message constraints, that are required to pass
for a message to be sent.

.. versionadded:: 4.1
"""
from __future__ import annotations
from abc import abstractmethod, ABC
from _discord import TextChannel

from .autochannel import AutoCHANNEL
from ..misc import doc_category


__all__ = ("AntiSpamMessageConstraint",)


class BaseMessageConstraint(ABC):
    @abstractmethod
    def check(self, channels: list[TextChannel]) -> list[TextChannel]:
        """
        Checks if the message can be sent based on the configured check.
        """


@doc_category("Message constraints")
class AntiSpamMessageConstraint(BaseMessageConstraint):
    """
    Prevents a new message to be sent if the last message in the same channel was
    sent by us, thus preventing spam on inactivate channels.

    .. versionadded:: 4.1
    """
    def __init__(self, per_channel: bool = True) -> None:
        self.per_channel = per_channel
        super().__init__()

    def check(self, channels: list[TextChannel | AutoCHANNEL]) -> list[TextChannel]:
        allowed = list(filter(
            lambda channel: channel.last_message is None or
            channel.last_message.author.id != channel._state.user.id, channels
        ))
        if not self.per_channel and len(allowed) != len(channels):  # In global mode, only allow to all channels
            return []

        return allowed
