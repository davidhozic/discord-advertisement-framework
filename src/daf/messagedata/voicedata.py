from dataclasses import dataclass, asdict

from .basedata import BaseMessageData
from ..misc.doc import doc_category
from .file import FILE


__all__ = ("BaseVoiceData", "VoiceMessageData",)


class BaseVoiceData(BaseMessageData):
    """
    Interface for voice-like / audio-like data.
    """


@doc_category("Message data", path="messagedata")
@dataclass
class VoiceMessageData(BaseVoiceData):
    """
    Represents fixed voice-like data.
    """
    file: FILE

    async def to_dict(self) -> dict:
        return asdict(self)
