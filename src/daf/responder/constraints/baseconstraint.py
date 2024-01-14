"""
Implements the base constraint.
"""

from abc import ABC, abstractmethod

import _discord as discord


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
