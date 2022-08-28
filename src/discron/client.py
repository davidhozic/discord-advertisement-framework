"""
    This modules contains definitions related to the client (for API)
"""

from typing import Optional
import _discord as discord
from .tracing import *
from . import core



#######################################################################
# Globals
#######################################################################
__all__ = (
    "CLIENT",
    "get_client"
)

class GLOBALS:
    "Storage class used for storing global variables"
    client = None     # Pycord Client object
    running = False # Weird bug causes client.on_ready method to be called multiple times some times
    proxy_installed = False

# ----------------- OPTIONAL ----------------- #
try:
    from aiohttp_socks import ProxyConnector
    GLOBALS.proxy_installed = True
except ImportError:
    GLOBALS.proxy_installed = False
# -------------------------------------------- #


class CLIENT(discord.Client):
    """
    The same as `discord.Client <https://docs.pycord.dev/en/master/api.html?highlight=client#discord.Client>`_,
    except it contains an on_ready coroutine.

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
                proxy: Optional[str],
                intents: discord.Intents):
    """

    Initializes the client module (Pycord).

    Parameters
    ----------------
    token: str
        Authorization token for connecting to discord.
    bot: bool
        Tells if the token is for a bot account.
    proxy: Optional[str]
        The proxy address to use.
    intents: discord.Intents
        The intents discord object. Intents are settings that
        dictate which dictates the events that the client will listen for.
    """
    connector = None
    if proxy is not None:
        if not GLOBALS.proxy_installed:
            raise ModuleNotFoundError("You need to install extra requirements: pip install discord-advert-framework[proxy]")
        
        connector = ProxyConnector.from_url(proxy)

    GLOBALS.client = CLIENT(intents=intents, connector=connector)
    if not bot:
        trace("[CLIENT]: Bot is an user account which is against discord's ToS",TraceLEVELS.WARNING)
    GLOBALS.client.run(token, bot=bot)


def get_client() -> CLIENT:
    """
    Returns the `CLIENT` object used for communicating with Discord.
    """
    return GLOBALS.client
