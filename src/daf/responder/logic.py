"""
Logical operations for keywords.
"""
from typing import List, Union
from abc import ABC, abstractmethod
from typeguard import typechecked


__all__ = (
    "BaseLogic",
    "and_",
    "or_",
)


class BaseLogic(ABC):
    @typechecked
    def __init__(
        self,
        operants: List[Union[str, "BaseLogic"]]
    ) -> None:
        self.operants = operants

    @abstractmethod
    def check(self, input: str):
        pass


class and_(BaseLogic):
    def check(self, input: str):
        for op in self.operants:
            if isinstance(op, BaseLogic):
                check = op.check(input)
            else:
                check = op in input

            if not check:
                return False

        return True


class or_(BaseLogic):
    def check(self, input: str):
        for op in self.operants:
            if isinstance(op, BaseLogic):
                check = op.check(input)
            else:
                check = op in input

            if check:
                return True

        return False
