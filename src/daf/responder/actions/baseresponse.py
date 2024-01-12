from abc import ABC, abstractmethod
from typing import List, Union
from typeguard import typechecked

from ...dtypes import FILE
from ...datamgr import TextDataManager

import _discord as discord


class BaseResponse(ABC):
    @typechecked
    def __init__(self, data: List[Union[str, discord.Embed, FILE]]) -> None:
        self.datamgr = TextDataManager(data)

    @abstractmethod
    async def perform(self, message: discord.Message):
        """
        Perform the action.

        Parameters
        -----------
        message: discord.Message
        """
        pass
