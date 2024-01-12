from _discord.message import Message
from .baseresponse import BaseResponse

import _discord as discord


class GuildResponse(BaseResponse):
    async def perform(self, message: Message):
        data = await self.datamgr._get_data()
        await message.reply(
            content=data["text"],
            embed=data["embed"],
            files=[discord.File(x) for x in data["files"]]
        )
