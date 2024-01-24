from abc import abstractmethod, ABC
from typing import TypedDict


__all__ = ("BaseMessageData",)


class BaseMessageData(ABC):
    """
    Interface for message data.
    The interface enforces the definition of ``to_dict`` method,
    which must return a ``TypedDict``.
    """

    @abstractmethod
    async def to_dict(self) -> TypedDict:
        pass

