from typing import List, Optional, Callable
from dataclasses import dataclass, asdict, field

from ..dtypes import FILE
from .basedata import BaseMessageData

import _discord as discord


__all__ = ("VoiceMessageData", "DynamicVoiceMessageData")


class BaseTextData(BaseMessageData):
    pass


@dataclass
class VoiceMessageData(BaseTextData):
    file: FILE

    async def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class DynamicVoiceMessageData(BaseTextData):
    getter: Callable[[], VoiceMessageData]

    async def to_dict(self) -> dict:
        return asdict(self)


