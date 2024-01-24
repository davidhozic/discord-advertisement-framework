from abc import abstractmethod
from typing import Coroutine

from .voicedata import BaseVoiceData, VoiceMessageData
from .textdata import BaseTextData, TextMessageData
from ..logging.tracing import trace, TraceLEVELS
from .basedata import BaseMessageData
from ..misc.doc import doc_category
from .file import FILE

from _discord import Embed


__all__ = ("DynamicMessageData",)


@doc_category("Message data", path="messagedata")
class DynamicMessageData(BaseTextData, BaseVoiceData):
    """
    Represents dynamic message data. Can be both text or voice,
    but make sure text is only used on :class:`~daf.message.TextMESSAGE` and
    voice on :class:`~daf.message.VoiceMESSAGE`.

    This needs to be inherited and the subclass needs to implement
    the ``get_data`` method, which accepts no parameters (pass those through the class).


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
        
        The method must return either a :class:`~daf.messagedata.TextMessageData` or
        a :class:`~daf.messagedata.VoiceMessageData` instance.
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
                    ########################################################
                    # DEPRECATED, compatibility only code! TODO: remove!
                    if not isinstance(result, (list, tuple, set)):
                        result = [result]

                    audio_data = dict(file=None)
                    text_data = dict(content=None, embed=None, files=[])
                    for item in result:
                        if isinstance(item, str):
                            text_data["content"] = item
                        elif isinstance(item, Embed):
                            text_data["embed"] = item
                        elif isinstance(item, FILE):
                            # A bit ambiguous, assume audio files are always mp3
                            if item.filename.endswith(".mp3"):
                                audio_data["file"] = item
                                break
                            else:
                                text_data["files"].append(item)

                    if any(text_data.values()):
                        return await TextMessageData(**text_data).to_dict()
                    if any(audio_data.values()):
                        return await VoiceMessageData(**audio_data).to_dict()
                    ########################################################

        except Exception as exc:
            trace("Error dynamically obtaining data", TraceLEVELS.ERROR, exc)

        return {}


class _DeprecatedDynamic(DynamicMessageData):
    def __init__(self, fnc, *args, **kwargs) -> None:
        self.args = args
        self.kwargs = kwargs
        self.fnc = fnc
    
    def get_data(self):
        return self.fnc(*self.args, **self.kwargs)
