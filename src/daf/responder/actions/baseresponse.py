from abc import ABC, abstractmethod
from typing import List, Union
from typeguard import typechecked

from ...dtypes import FILE
from ...messagedata import BaseTextData

import _discord as discord


class BaseResponse(ABC):
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
