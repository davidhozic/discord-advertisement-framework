"""
    ~  client  ~
    This modules contains definitions
    related to the client (for API)
"""

import  asyncio
import  _discord as discord
from    .tracing import *
from    . import core



#######################################################################
# Globals
#######################################################################
m_client                 = None     # Pycord Client object

__all__ = (
    "CLIENT",
    "get_client"
)


class CLIENT(discord.Client):
    """
        Name : CLIENT
        Info : Inherited class from discord.Client.
               Contains an additional on_ready function.
    """
    async def on_ready(self) -> None:
        """
            Name : on_ready
            Info : Tasks that is started by pycord when you have been
                   successfully logged into discord.
        """
        trace(f"Logged in as {self.user}", TraceLEVELS.NORMAL)

        if core.GLOBALS.user_callback is not None:   # If user callback function was specified
            await core.GLOBALS.user_callback() # Call user provided function after framework has started

        if await core.initialize():
            # Initialization was successful, so create the advertiser task and start advertising.
            trace("Successful initialization!",TraceLEVELS.NORMAL)
            asyncio.gather(
                # Tasks for sending text messages/voice messages
                asyncio.create_task(core.advertiser("text")),
                asyncio.create_task(core.advertiser("voice"))
            )
        else:
            # Initialization failed, close everything
            await core.shutdown()


def initialize(token: str, *,
               bot: bool):
    """
        ~  initialize  ~
        @Param:
        - token: str ~ authorization token for connecting to discord
        - bot: bool ~ bool variable that should be True if the token
                      is for a bot account and False if the token is
                      for an user account.
        @Info:
        The function initializes Pycord, the discord API wrapper.
    """
    global m_client
    intents = discord.Intents.all()
    m_client = CLIENT(intents=intents)
    if not bot:
        trace("Bot is an user account which is against discord's ToS",TraceLEVELS.WARNING)
    m_client.run(token, bot=bot)


def get_client() -> CLIENT:
    """
    Name:   get_client
    Params: void
    Return: discord.Client | None
    Info:   Returns the client object used by the framework,
            so the user wouldn't have to run 2 clients.
    """
    return m_client
