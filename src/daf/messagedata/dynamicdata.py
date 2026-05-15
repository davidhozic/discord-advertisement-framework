from abc import abstractmethod
from typing import Coroutine

from .textdata import BaseTextData
from ..logging.tracing import trace, TraceLEVELS
from .basedata import BaseMessageData
from ..misc.doc import doc_category
from .file import FILE

from _discord import Embed


__all__ = ("DynamicMessageData",)


@doc_category("Message data", path="messagedata")
class DynamicMessageData(BaseTextData):
    """
    Represents dynamic message data. Can be both text or voice,
    but make sure text is only used on :class:`~daf.message.TextMESSAGE`.

    This needs to be inherited and the subclass needs to implement
    the ``get_data`` method, which accepts no parameters (pass those through the class).

    .. versionchanged:: v4.2.0

        The method ``get_data`` no longer allows data to be returned in the deprecated format.
        Now :class:`daf.messagedata.TextMessageData`.
        must be returned.

    Example
    -------------
    .. code-block:: python

        class MyCustomText(DynamicMessageData):
            def __init__(self, a: int):
                self.a = a

            def get_data(self):  # Can also be async
                return TextMessageData(f"Passed parameter was: {self.a}")

        
        TextMESSAGE(data=MyCustomText(152))
    """
   
    @abstractmethod
    def get_data(self) -> BaseMessageData:
        """
        The data getter method.
        Needs to be implemented in a subclass.
        
        The method must returns a :class:`~daf.messagedata.TextMessageData`.
        It can also return ``None`` if no data is to be sent.
        """
        pass

    async def to_dict(self) -> dict:
        try:
            result = self.get_data()
            if isinstance(result, Coroutine):
                result = await result
    
            if result is not None:
                if isinstance(result, BaseMessageData):
                    return await result.to_dict()
                else:
                    trace(
                        "Instance of DynamicMessageData returned invalid data.\n"
                        "Only None (to ignore), TextMessageData are allowed.",
                        TraceLEVELS.ERROR,
                    )

        except Exception as exc:
            trace("Error dynamically obtaining data", TraceLEVELS.ERROR, exc)

        return {}
