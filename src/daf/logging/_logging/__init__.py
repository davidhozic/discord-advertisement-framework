"""
Dummy module for serialization decoding compatibility with older versions.
"""
from ..logger_base import *
from ..logger_json import *
from ..logger_csv import *


from typing import Optional

from ..tracing import trace, TraceLEVELS
from ...misc import doc


class GLOBAL:
    "Singleton for global variables"
    logger = None


__all__ = (
    "get_logger",
    "save_log",
    "LoggerJSON",
    "LoggerCSV",
    "LoggerBASE"
)


async def initialize(logger: LoggerBASE) -> None:
    """
    Initialization coroutine for the module.

    Parameters
    --------------
    The logger manager to use for saving logs.
    """
    while logger is not None:
        try:
            await logger.initialize()
            break
        except Exception as exc:
            trace(f"Could not initialize manager {type(logger).__name__}, falling to {type(logger.fallback).__name__}",
            TraceLEVELS.WARNING, exc)
            logger = logger.fallback # Could not initialize, try fallback
    else:
        trace("Logging will be disabled as the logging manager and it's fallbacks all failed initialization",
              TraceLEVELS.ERROR)

    GLOBAL.logger = logger


@doc.doc_category("Logging reference", path="logging")
def get_logger() -> LoggerBASE:
    """
    Returns
    ---------
    LoggerBASE
        The selected logging object which is of inherited type from LoggerBASE.
    """
    return GLOBAL.logger


def _set_logger(logger: LoggerBASE):
    """
    Set's the logger to something new.

    Parameters
    -------------
    logger: LoggerBASE
        The logger to use.
    """
    GLOBAL.logger = logger


async def save_log(
    guild_context: dict,
    message_context: Optional[dict] = None,
    author_context: Optional[dict] = None,
    invite_context: Optional[dict] = None
):
    """
    Saves the log to the selected manager or saves
    to the fallback manager if logging fails to the selected.

    Parameters
    ------------
    guild_context: dict
        Information about the guild.
    message_context: Optional[dict]
        Information about the message sent.
    author_context: Optional[dict]
        Information about the message author (ACCOUNT).
    invite_context: Optional[dict].
        Information about a new guild join by invite.
    """
    mgr: LoggerBASE = GLOBAL.logger

    # Don't spam the console if no loggers are available
    if mgr is None:
        return

    while mgr is not None:
        try:
            await mgr._save_log(guild_context, message_context, author_context, invite_context)
            break
        except Exception as exc:
            trace(
                f"{type(mgr).__name__} failed, falling to {type(mgr.fallback).__name__}",
                TraceLEVELS.WARNING,
                exc
            )
            mgr = mgr.fallback  # Could not initialize, try fallback
    else:
        trace("Could not save log to the manager or any of it's fallback", TraceLEVELS.ERROR)
