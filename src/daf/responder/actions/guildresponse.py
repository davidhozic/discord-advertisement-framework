from _discord.message import Message
from .baseresponse import BaseResponse

import _discord as discord


class GuildResponse(BaseResponse):
    async def perform(self, message: Message):
        data = await self.data.to_dict()
        await message.reply(
            content=data["content"],
            embed=data["embed"],
            files=[discord.File(x) for x in data["files"]]
        )
