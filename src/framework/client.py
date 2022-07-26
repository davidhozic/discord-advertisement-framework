"""
    This modules contains definitions related to the client (for API)
"""

import  asyncio
import  _discord as discord
from    .tracing import *
from    . import core


#######################################################################
# Globals
#######################################################################
class GLOBALS:
    client = None     # Pycord Client object
    running = False # Weird bug causes client.on_ready method to be called multiple times some times

__all__ = (
    "CLIENT",
    "get_client"
)


class CLIENT(discord.Client):
    """
    The same as `discord.Client <https://docs.pycord.dev/en/master/api.html?highlight=client#discord.Client>`_, except it contains an on_ready coroutine.

    .. note::
        This is automatically created by the framework.
        You can retrieve the object created by calling :ref:`get_client` function.
    """
    async def on_ready(self) -> None:
        """
        Gets run at login, creates the main initialization task inside the core module.
        """
        if GLOBALS.running:
            return

        GLOBALS.running = True
        trace(f"[CLIENT]: Logged in as {self.user}", TraceLEVELS.NORMAL)
        # Initialize all the modules from the core module
        self.loop.create_task(core._initialize())
        

def _initialize(token: str, *,
               bot: bool,
               intents: discord.Intents):
    """
    
    Initializes the client module (Pycord).

    Parameters
    ----------------
    token: str
        Authorization token for connecting to discord.
    bot: bool
        Tells if the token is for a bot account.
                      and False if the token is  for an user account.
    intents: discord.Intents
        The intents discord object. Intents are settings that
                                    dictate which dictates the events that the client will listen for.
    """
    GLOBALS.client = CLIENT(intents=intents)
    if not bot:
        trace("[CLIENT]: Bot is an user account which is against discord's ToS",TraceLEVELS.WARNING)
    GLOBALS.client.run(token, bot=bot)


def get_client() -> CLIENT:
    """
    Returns the `CLIENT` object used for communicating with Discord.
    """
    return GLOBALS.client
