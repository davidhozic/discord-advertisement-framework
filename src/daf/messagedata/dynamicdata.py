from typing import Coroutine
from abc import abstractmethod

from .basedata import BaseMessageData
from .textdata import BaseTextData
from .voicedata import BaseVoiceData
from ..misc.doc import doc_category
from ..logging.tracing import trace, TraceLEVELS


__all__ = ("DynamicMessageData",)


@doc_category("Message data", path="messagedata")
class DynamicMessageData(BaseTextData, BaseVoiceData):
    """
    Represents dynamic message data. Can be both text or voice,
    but make sure text is only used on ``TextMESSAGE`` and voice on ``VoiceMESSAGE``

    This needs to be inherited and the subclass needs to implement
    the ``get_data`` method, which accepts no parameters (pass those through the class) and
    returns :class:`daf.messagedata.TextMessageData`.

    Example
    -------------

    .. code-block:: python

        class MyCustomText(DynamicMessageData):
            def __init__(self, a: int):
                self.a = a

            def get_data(self):  # Can also be async
                return TextMessageData(f"Passed parameter was: {self.a}")

        
        class MyCustomVoice(DynamicMessageData):
            def get_data(self):  # Can also be async
                return VoiceMessageData(FILE("./audio.mp3"))

        
        TextMESSAGE(data=MyCustomText(152))
        VoiceMESSAGE(data=MyCustomVoice())        
    """
   
    @abstractmethod
    def get_data(self) -> BaseMessageData:
        """
        The data getter method.
        Needs to be implemented in a subclass.
        
        The method must return either a ``TextMessageData`` or a ``VoiceMessageData`` object.
        It can also return ``None`` if no data is to be sent.
        """
        pass

    async def to_dict(self) -> dict:
        try:
            result = self.get_data()
            if isinstance(result, Coroutine):
                result = await result
    
            if result is not None:
                return await result.to_dict()
        except Exception as exc:
            trace("Error dynamically obtaining data", TraceLEVELS.ERROR, exc)

        return {}
