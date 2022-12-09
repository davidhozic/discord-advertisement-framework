"""
    This modules contains definitions related to the client (for API)
"""
from __future__ import annotations
from typing import Optional, Union, Optional, Callable, Coroutine, List

from . import misc
from . import guild
from . import logging

from .logging.tracing import *

import _discord as discord
import asyncio


#######################################################################
# Globals
#######################################################################
LOGIN_TIMEOUT_S = 30
TOKEN_MAX_PRINT_LEN = 5
TASK_SLEEP_DELAY_MS = 100

__all__ = (
    "get_client",
)

class GLOBALS:
    "Storage class used for storing global variables"
    proxy_installed = False


# ----------------- OPTIONAL ----------------- #
try:
    from aiohttp_socks import ProxyConnector
    GLOBALS.proxy_installed = True
except ImportError:
    GLOBALS.proxy_installed = False
# -------------------------------------------- #


class ACCOUNT:
    """
    Represents an individual Discord account.
    
    Each ACCOUNT instance runs it's own shilling task.
    """
    def __init__(
                self,
                token : str,
                is_user : Optional[bool] =False,
                servers: Optional[List[guild.GUILD | guild.USER | guild.AutoGUILD]]=[],
                intents: Optional[discord.Intents]=None,
                proxy: Optional[str]=None) -> None:
        self.token = token
        self.is_user = is_user
        self.proxy = proxy
        self.tasks = {
            "client": None,
            "text": None,
            "voice": None
        }
        self.servers = servers
        connector = None
        if proxy is not None:
            if not GLOBALS.proxy_installed:
                raise ModuleNotFoundError("You need to install extra requirements: pip install discord-advert-framework[proxy]")
        
            connector = ProxyConnector.from_url(proxy)

        self.client = discord.Client(intents=intents, connector=connector)

    async def initialize(self):
        """
        Initializes the API wrapper client layer.

        Raises
        ------------
        RuntimeError
            Unable to login to Discord.

        """
        # Login
        self.tasks["client"] = asyncio.create_task(self.client.start(self.token, bot=self.is_user))
        try:
            await self.client.wait_for("ready", timeout=LOGIN_TIMEOUT_S)
        except asyncio.TimeoutError:
            exc = self.tasks["client"].exception()
            raise RuntimeError(f"Error logging in to Discord. (Token {self.token[:TOKEN_MAX_PRINT_LEN]}...)") from exc
        
        for server in self.servers:
            try:
                await self.add_object(server)
            except Exception as exc:
                trace(exc, TraceLEVELS.WARNING)

    async def _loop(self, type_: guild.AdvertiseTaskType):
        """
        Main task loop for advertising thru each guild.
        2 tasks are running as this method.

        Parameters
        -------------
        type_:  guild.AdvertiseTaskType
            Task type (for text messages of voice messages)
        """
        while True:
            await asyncio.sleep(TASK_SLEEP_DELAY_MS)
            # Sum, creates new list, making modifications on original lists safe
            for guild_user in self.server_list + self.auto_guilds: 
                # Remove guild
                if guild_user._check_state():
                    # remove guild user
                    pass
                else:
                    await guild_user._advertise(type_)

    async def add_object(self, object_: guild.GUILD | guild.USER | guild.AutoGUILD, snowflake):
        pass # TODO: add message.BaseMESSAGE to annotations, fill code
        


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
    connector = None
    if proxy is not None:
        if not GLOBALS.proxy_installed:
            raise ModuleNotFoundError("You need to install extra requirements: pip install discord-advert-framework[proxy]")
        
        connector = ProxyConnector.from_url(proxy)

    GLOBALS.client = discord.Client(intents=intents, connector=connector)
    _client = GLOBALS.client
    if not bot:
        trace("[CLIENT]: Bot is an user account which is against discord's ToS",TraceLEVELS.WARNING)

    asyncio.create_task(_client.start(token, bot=bot))
    await _client.wait_for("ready")


@misc.doc_category("Getters")
def get_client() -> discord.Client:
    """
    Returns the `CLIENT` object used for communicating with Discord.
    """
    return GLOBALS.client
