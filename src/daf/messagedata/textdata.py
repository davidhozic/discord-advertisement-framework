from typing import List, Optional, Optional
from dataclasses import dataclass, asdict, field

from .basedata import BaseMessageData
from ..misc.doc import doc_category
from .file import FILE

import _discord as discord


__all__ = ("BaseTextData", "TextMessageData",)


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
