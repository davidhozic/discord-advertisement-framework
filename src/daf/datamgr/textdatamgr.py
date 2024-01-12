from typing import List, Dict, Union, TypedDict, Optional
from typeguard import typechecked

from .basedatamgr import BaseDataManager
from ..dtypes import FILE

import _discord as discord


class DataDict(TypedDict):
    text: Optional[str]
    embed: Optional[discord.Embed]
    files: List[FILE]


class TextDataManager(BaseDataManager):
    @typechecked
    def __init__(self, data: List[Union[str, discord.Embed, FILE]]) -> None:
        self._verify_data(data)
        super().__init__(data)

    @staticmethod
    def _verify_data(data: List[Union[str, discord.Embed, FILE]]):
        data = [type(x) for x in data]

        if data.count(str) > 1:
            raise ValueError("There can only be one text (str) content.")
        
        if data.count(discord.Embed) > 1:
            raise ValueError("There can only be one Embed element.")

        if data.count(FILE) > 10:
            raise ValueError("There can only maximum of 10 files.")

    async def _get_data(self) -> DataDict:
        data = await super()._get_data()
        _data_to_send: Dict[str, Union[List, discord.Embed, str]] = {"embed": None, "text": None, "files": []}
        if data is not None:
            if not isinstance(data, (list, tuple, set)):
                data = (data,)

            for element in data:
                if isinstance(element, str):
                    _data_to_send["text"] = element
                elif isinstance(element, discord.Embed):
                    _data_to_send["embed"] = element
                elif isinstance(element, FILE):
                    _data_to_send["files"].append(element)

        return _data_to_send
