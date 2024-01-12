from typing import List, Optional, Callable
from dataclasses import dataclass, asdict, field

from ..dtypes import FILE
from .basedata import BaseMessageData

import _discord as discord


__all__ = ("BaseTextData", "TextMessageData", "DynamicTextMessageData")


class BaseTextData(BaseMessageData):
    pass


@dataclass
class TextMessageData(BaseTextData):
    content: Optional[str] = None
    embed: Optional[discord.Embed] = None
    files: List[FILE] = field(default_factory=list)

    async def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class DynamicTextMessageData(BaseTextData):
    getter: Callable[[], TextMessageData]

    async def to_dict(self) -> dict:
        return asdict(self)


