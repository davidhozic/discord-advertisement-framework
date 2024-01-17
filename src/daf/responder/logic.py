"""
Logical operations for keywords.
"""
from __future__ import annotations
from typing import List, Optional
from abc import ABC, abstractmethod
from typeguard import typechecked

import re


__all__ = (
    "and_",
    "or_",
    "not_",
    "contains",
    "regex",
)


class BaseLogic(ABC):
    """
    A logic interface for building keyword expressions.
    """
    @abstractmethod
    def check(self, input: str):
        pass


class BooleanLogic(BaseLogic):
    """
    A logic abstract class that accepts multiple logic elements.
    It represents boolean logic (and, or, not).
    """
    @typechecked
    def __init__(
        self,
        operants: List[BaseLogic]
    ) -> None:
        self.operants = operants


class and_(BooleanLogic):
    def check(self, input: str):
        for op in self.operants:
            if isinstance(op, BaseLogic):
                check = op.check(input)
            else:
                check = op in input

            if not check:
                return False

        return True


class or_(BooleanLogic):
    def check(self, input: str):
        for op in self.operants:
            if isinstance(op, BaseLogic):
                check = op.check(input)
            else:
                check = op in input

            if check:
                return True

        return False


class not_(BooleanLogic):
    def __init__(self, operant: BaseLogic) -> None:
        super().__init__([operant])

    def check(self, input: str):
        op = self.operants[0]
        if isinstance(op, BaseLogic):
            return not op.check(input)

        return op not in input


class contains(BaseLogic):
    def __init__(self, keyword: str) -> None:
        self.keyword = keyword

    def check(self, input: str):
        return self.keyword in input.split()


class regex(BaseLogic):
    def __init__(
        self,
        pattern: str,
        flags: Optional[re.RegexFlag] = re.DOTALL | re.MULTILINE,
        full_match: bool = False
    ) -> None:
        self._full_match = full_match
        self._compiled: re.Pattern = re.compile(pattern.strip(), flags)
        self._checker = re.fullmatch if full_match else re.search

    @property
    def pattern(self):
        return self._compiled.pattern

    @property
    def flags(self):
        return self._compiled.flags

    @property
    def full_match(self):
        return self._full_match

    def check(self, input: str):
        return self._checker(self._compiled, input)
