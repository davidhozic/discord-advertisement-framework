"""
Implements the base constraint.
"""
from abc import ABC, abstractmethod

from ...misc.doc import doc_category

import _discord as discord


__all__ = ("ConstraintBase", )

@doc_category("Auto responder")
class ConstraintBase(ABC):
    @abstractmethod
    def check(self, message: discord.Message, client: discord.Client) -> bool:
        """
        Verifies if the constraint is fulfilled.

        Parameters
        -------------
        message: :class:`discord.Message`
            Potential message to be responded to.
        """
        pass
