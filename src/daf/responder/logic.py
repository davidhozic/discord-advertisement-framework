"""
Logical operations for keywords.
"""
from __future__ import annotations
from typing import List
from abc import ABC, abstractmethod
from typeguard import typechecked

from ..misc.doc import doc_category

import re


__all__ = (
    "and_",
    "or_",
    "not_",
    "contains",
    "regex",
)


@doc_category("Auto responder")
class BaseLogic(ABC):
    """
    A logic interface for building keyword expressions.
    """
    @abstractmethod
    def check(self, input: str) -> bool:
        pass


@doc_category("Auto responder")
class BooleanLogic(BaseLogic):
    """
    Represents boolean logic.

    Parameters
    -------------
    args: Unpack[BaseLogic]
        Arbitrary number of operants (either logic boolean or text operants).
    """
    @typechecked
    def __init__(
        self,
        *args,
        operants: List[BaseLogic] = [],
    ) -> None:
        self.operants = [*operants, *args]


@doc_category("Auto responder")
class and_(BooleanLogic):
    """
    Represents logical *AND* operator.

    Parameters
    -------------
    args: Unpack[BaseLogic]
        Arbitrary number of operants (either logic boolean or text operants).
    """

    def check(self, input: str):
        for op in self.operants:
            if isinstance(op, BaseLogic):
                check = op.check(input)
            else:
                check = op in input

            if not check:
                return False

        return True


@doc_category("Auto responder")
class or_(BooleanLogic):
    """
    Represents logical *OR* operator.

    Parameters
    -------------
    args: Unpack[BaseLogic]
        Arbitrary number of operants (either logic boolean or text operants).
    """
    def check(self, input: str):
        for op in self.operants:
            if isinstance(op, BaseLogic):
                check = op.check(input)
            else:
                check = op in input

            if check:
                return True

        return False


@doc_category("Auto responder")
class not_(BooleanLogic):
    """
    Represents logical *NOT* operator.

    Parameters
    -------------
    operant: BaseLogic
        A single operant to negate.
    """

    def __init__(self, operant: BaseLogic) -> None:
        super().__init__(operant)

    def check(self, input: str):
        op = self.operants[0]
        if isinstance(op, BaseLogic):
            return not op.check(input)

        return op not in input


@doc_category("Auto responder")
class contains(BaseLogic):
    """
    Text matching condition.

    Parameters
    ---------------
    keyword: str
        The keyword needed to be inside a text message.
    """
    def __init__(self, keyword: str) -> None:
        self.keyword = keyword.lower()

    def check(self, input: str):
        return self.keyword in re.findall(r'\w+', input)  # \w+ == match all words, including **bold**


@doc_category("Auto responder")
class regex(BaseLogic):
    """
    RegEx (regular expression) text matching condition.

    Parameters
    -------------
    pattern: str
        The RegEx pattern string.
    flags: Optional[re.RegexFlag]
        RegEx (binary) flags.
        Defaults to re.MULTILINE.
    full_match: Optional[bool]
        Boolean parameter. If True, the ``pattern`` must capture
        the entire text message string for a match.
        Defaults to False.
    """
    def __init__(
        self,
        pattern: str,
        flags: re.RegexFlag = re.MULTILINE,
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
        return self._checker(self._compiled, input) is not None
