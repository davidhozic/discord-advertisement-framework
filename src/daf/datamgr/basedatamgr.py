from typing import Any
from abc import ABC, abstractmethod
from ..dtypes import _FunctionBaseCLASS



class BaseDataManager(ABC):
    def __init__(self, data: Any) -> None:
        self.data = data
        self.fbc_data = isinstance(data, _FunctionBaseCLASS)

    async def _get_data(self) -> dict:
        data = self.data
        if self.fbc_data:
            data = data.retrieve()

        return data
