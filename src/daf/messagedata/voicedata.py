from typing import List, Callable, Any, Dict
from dataclasses import dataclass, asdict

from ..dtypes import FILE
from .basedata import BaseMessageData

__all__ = ("VoiceMessageData", "DynamicVoiceMessageData")


class BaseTextData(BaseMessageData):
    pass


@dataclass
class VoiceMessageData(BaseTextData):
    file: FILE

    async def to_dict(self) -> dict:
        return asdict(self)


@dataclass(init=False)
class DynamicVoiceMessageData(BaseTextData):
    getter: Callable[[], VoiceMessageData]
    args: List[Any]
    kwargs: Dict[str, Any]

    def __init__(self, getter: Callable[[], VoiceMessageData], *args, **kwargs):
        self.getter = getter
        self.args = args
        self.kwargs = kwargs

    async def to_dict(self) -> dict:
        return asdict(self)


