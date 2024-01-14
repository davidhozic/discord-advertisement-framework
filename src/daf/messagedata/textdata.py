from typing import List, Optional, Callable, Any, Dict
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


@dataclass(init=False)
class DynamicTextMessageData(BaseTextData):
    getter: Callable[[], TextMessageData]
    args: List[Any]
    kwargs: Dict[str, Any]

    def __init__(self, getter: Callable[[], TextMessageData], *args, **kwargs):
        self.getter = getter
        self.args = args
        self.kwargs = kwargs

    async def to_dict(self) -> dict:
        return asdict(self)

