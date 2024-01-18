from typing import List, Callable, Any, Dict, Coroutine
from dataclasses import dataclass, asdict

from ..dtypes import FILE
from .basedata import BaseMessageData
from ..misc.doc import doc_category
from ..misc.async_util import except_return


__all__ = ("VoiceMessageData", "DynamicVoiceMessageData")


@doc_category("Message data", path="messagedata")
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


@doc_category("Message data", path="messagedata")
@dataclass(init=False)
class DynamicVoiceMessageData(BaseVoiceData):
    """
    Represents dynamic voice-like data.
    """

    getter: Callable[[], VoiceMessageData]
    args: List[Any]
    kwargs: Dict[str, Any]

    def __init__(self, getter: Callable[[], VoiceMessageData], *args, **kwargs):
        self.getter = getter
        self.args = args
        self.kwargs = kwargs

    @except_return
    async def to_dict(self) -> dict:
        result = self.getter(*self.args, **self.kwargs)
        if isinstance(result, Coroutine):
            result = await result

        if isinstance(result, VoiceMessageData):
            return await result.to_dict()

        return None
