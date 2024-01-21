from typing import List, Optional, Callable, Any, Dict, Coroutine, Optional
from dataclasses import dataclass, asdict, field
from datetime import timedelta, datetime

from ..dtypes import FILE
from .basedata import BaseMessageData
from ..misc.doc import doc_category
from ..logging.tracing import trace, TraceLEVELS

import _discord as discord


__all__ = ("BaseTextData", "TextMessageData", "DynamicTextMessageData", "CountdownTextMessageData")


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


@doc_category("Message data", path="messagedata")
class CountdownTextMessageData(DynamicTextMessageData):
    """
    Dynamic text message data that counts down.
    The countdown timer is added next to the original text message data.

    **NOTE** - This should only be used on xMESSAGE objects. Using it on an automatic responder will NOT
    produce a continuous timer output but rather a single message per each response, where each response
    will send the current countdown value.

    Parameters
    --------------
    delta: timedelta
        The countdown's initial value.
    static: Optional[TextMessageData]
        Static data that is going to be send.
    """
    def __init__(self, delta: timedelta, static: Optional[TextMessageData] = None):
        super().__init__(self._get_next_count)

        if static is None:
            static = TextMessageData()

        self.delta = delta

        if static.content is None:
            static.content = ""  # Prevent unnecessary checks when obtaining

        self.static = static

        self._last_time = None
        self._countdown_live = delta

    async def _get_next_count(self):
        static = await self.static.to_dict()
        now_time = datetime.now()
        if self._last_time is None:
            self._last_time = now_time

        self._countdown_live = max(self._countdown_live - (now_time - self._last_time), timedelta())
        self._last_time = now_time
        countdown = self._countdown_live
        info = (
            countdown.days,
            countdown.seconds // 3600,
            (countdown.seconds // 60) % 60,
            countdown.seconds % 60
        )
        info_names = ("day", "hour", "minute", "second")
        first_non_zero = 3
        for i, num in enumerate(info):
            if num != 0:
                first_non_zero = i
                break

        time_str = ' '.join(
            f"{info[i]} {info_names[i] + ('s' if info[i] != 1 else '')}"
            for i in range(first_non_zero, len(info))
        )
        static["content"] = static["content"] + "\n\n" + time_str
        return TextMessageData(**static)
