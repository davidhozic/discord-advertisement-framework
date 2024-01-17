from typing import List, Optional, Callable, Any, Dict, Coroutine
from dataclasses import dataclass, asdict, field

from ..dtypes import FILE
from .basedata import BaseMessageData
from ..misc.doc import doc_category
from ..misc.async_util import except_return

import _discord as discord


__all__ = ("BaseTextData", "TextMessageData", "DynamicTextMessageData")


@doc_category("Message data", path="messagedata")
class BaseTextData(BaseMessageData):
    """
    Interface for text message data.
    """


@doc_category("Message data", path="messagedata")
@dataclass
class TextMessageData(BaseTextData):
    """
    Represents fixed text message data.
    """

    content: Optional[str] = None
    embed: Optional[discord.Embed] = None
    files: List[FILE] = field(default_factory=list)

    async def to_dict(self) -> dict:
        return asdict(self)


@doc_category("Message data", path="messagedata")
@dataclass(init=False)
class DynamicTextMessageData(BaseTextData):
    """
    Represents dynamic text message data.
    """
    getter: Callable[[], TextMessageData]
    args: List[Any]
    kwargs: Dict[str, Any]

    def __init__(self, getter: Callable[[], TextMessageData], *args, **kwargs):
        self.getter = getter
        self.args = args
        self.kwargs = kwargs

    @except_return
    async def to_dict(self) -> dict:
        result = self.getter(*self.args, **self.kwargs)
        if isinstance(result, Coroutine):
            result = await result

        if isinstance(result, TextMessageData):
            return await result.to_dict()

        return None
