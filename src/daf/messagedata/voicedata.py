from typing import List, Callable, Any, Dict, Coroutine
from dataclasses import dataclass, asdict
from contextlib import suppress

from ..dtypes import FILE
from .basedata import BaseMessageData
from ..misc.doc import doc_category
from ..logging.tracing import trace, TraceLEVELS


__all__ = ("BaseVoiceData", "VoiceMessageData", "DynamicVoiceMessageData")


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

    async def to_dict(self) -> dict:
        try:
            result = self.getter(*self.args, **self.kwargs)
            if isinstance(result, Coroutine):
                result = await result

            if isinstance(result, VoiceMessageData):
                return await result.to_dict()
            elif result is not None:
                # Compatibility with older type of 'data' parameter. TODO: Remove in future version (v4.2.0).
                if not isinstance(result, (list, tuple, set)):
                    result = [result]

                file = None
                if isinstance(result[0], FILE):
                    file = result[0]

                return await VoiceMessageData(file).to_dict()
        except Exception as exc:
            trace("Error dynamically obtaining data", TraceLEVELS.ERROR, exc)

        return {}
