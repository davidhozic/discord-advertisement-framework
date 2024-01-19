from typing import List, Optional, Callable, Any, Dict, Coroutine
from dataclasses import dataclass, asdict, field
from contextlib import suppress

from ..dtypes import FILE
from .basedata import BaseMessageData
from ..misc.doc import doc_category
from ..logging.tracing import trace, TraceLEVELS

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

    async def to_dict(self) -> dict:
        try:
            result = self.getter(*self.args, **self.kwargs)
            if isinstance(result, Coroutine):
                result = await result
    
            if isinstance(result, TextMessageData):
                return await result.to_dict()

            elif result is not None:
                # Compatibility with older type of 'data' parameter. TODO: Remove in future version (v4.2.0).
                if not isinstance(result, (list, tuple, set)):
                    result = [result]

                content, embed, files = None, None, []
                for item in result:
                    if isinstance(item, str):
                        content = item
                    elif isinstance(item, discord.Embed):
                        embed = item
                    elif isinstance(item, FILE):
                        files.append(item)

                return await TextMessageData(content, embed, files).to_dict()
        except Exception as exc:
            trace("Error dynamically obtaining data", TraceLEVELS.ERROR, exc)

        return {}
