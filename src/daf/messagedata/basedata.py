from abc import abstractmethod, ABC
from typing import TypedDict

__all__ = ("BaseMessageData",)

class BaseMessageData(ABC):
    @abstractmethod
    async def to_dict(self) -> TypedDict:
        pass

