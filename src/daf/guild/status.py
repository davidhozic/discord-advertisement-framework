"""
GUILD status module
"""
from enum import Enum, auto

__all__ = ("GuildAdvertStatus",)


class GuildAdvertStatus(Enum):
    SUCCESS = 0
    REMOVE_ACCOUNT = auto()
