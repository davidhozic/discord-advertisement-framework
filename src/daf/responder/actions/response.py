from abc import ABC, abstractmethod
from typeguard import typechecked

from ...messagedata import BaseTextData
from ...misc.doc import doc_category

import _discord as discord


__all__ = ("BaseResponse", "DMResponse", "GuildResponse")


@doc_category("Auto responder")
class BaseResponse(ABC):
    """
    Base response class.

    Parameters
    ----------------
    data: BaseTextData
        The data that can be sent into the text / DM channel.
    """
    @typechecked
    def __init__(self, data: BaseTextData) -> None:
        self.data = data

    @abstractmethod
    async def perform(self, message: discord.Message):
        """
        Perform the action.

        Parameters
        -----------
        message: discord.Message
        """
        pass


@doc_category("Auto responder")
class DMResponse(BaseResponse):
    """
    DM response class. Used for responding into DM messages
    of the message's author.

    Parameters
    ----------------
    data: BaseTextData
        The data that will be sent into message author's DM channel.
    """  
    async def perform(self, message: discord.Message):
        data = await self.data.to_dict()
        await message.author.send(
            content=data["content"],
            embed=data["embed"],
            files=[discord.File(x.stream, filename=x.filename) for x in data["files"]]
        )


@doc_category("Auto responder")
class GuildResponse(BaseResponse):
    """
    Guild response class. Used for responding into the same channel
    as the message that triggered the response.
    The response is a reply.

    Parameters
    ----------------
    data: BaseTextData
        The data that will be sent into the channel.
    """  
    async def perform(self, message: discord.Message):
        data = await self.data.to_dict()
        await message.reply(
            content=data["content"],
            embed=data["embed"],
            files=[discord.File(x.stream, filename=x.filename) for x in data["files"]]
        )
