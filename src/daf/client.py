"""
    This modules contains definitions related to the client (for API)
"""

from typing import Optional
from .tracing import *
import _discord as discord
import asyncio


#######################################################################
# Globals
#######################################################################
__all__ = (
    "get_client",
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

async def _initialize(token: str, *,
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
    login_event = asyncio.Event()

    async def on_ready():
        """
        Coroutine used to set the login event,
        which notifies the upper layer to continue
        with it's initialization.
        """
        login_event.set()

    connector = None
    if proxy is not None:
        if not GLOBALS.proxy_installed:
            raise ModuleNotFoundError("You need to install extra requirements: pip install discord-advert-framework[proxy]")
        
        connector = ProxyConnector.from_url(proxy)

    GLOBALS.client = discord.Client(intents=intents, connector=connector, bot=bot)
    _client = GLOBALS.client
    if not bot:
        trace("[CLIENT]: Bot is an user account which is against discord's ToS",TraceLEVELS.WARNING)

    _client.event(on_ready)
    await _client.login(token)
    asyncio.create_task(_client.connect())
    await login_event.wait() # Wait for the login to complete and the discord lib to initialize.


def get_client() -> discord.Client:
    """
    Returns the `CLIENT` object used for communicating with Discord.
    """
    return GLOBALS.client
