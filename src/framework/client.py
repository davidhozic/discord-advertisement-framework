from    .tracing import *
from    . import core
from    typing import Optional, Any
import  _discord as discord
import  asyncio


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
    def __init__(self, *, loop: Optional[asyncio.AbstractEventLoop] = None, **options: Any):
        super().__init__(loop=loop, **options)

    async def on_ready(self) -> None:
        """
        Name : on_ready
        Info : Tasks that is started by pycord when you have been successfully logged into discord.
        """
        trace(f"Logged in as {self.user}", TraceLEVELS.NORMAL)

        if await core.initialize():
            # Initialization was successful, so create the advertiser task and start advertising.
            trace("Successful initialization!",TraceLEVELS.NORMAL)
            asyncio.gather(
                    asyncio.create_task(core.advertiser("t_messages")),  # Task for sending text messages
                    asyncio.create_task(core.advertiser("vc_messages"))  # Task for sending voice messages
                )
        else:
            # Initialization failed, close everything
            await core.shutdown()

        if core.m_user_callback:   # If user callback function was specified
            core.m_user_callback() # Call user provided function after framework has started



#######################################################################
# Globals
#######################################################################
m_client                 = None     # Pycord Client object


def initialize(token: str, *,
               bot: bool):
    global m_client
    intents = discord.Intents.default()
    intents.members = True
    m_client = CLIENT(intents=intents)
    if not bot:
        trace("Bot is an user account which is against discord's ToS",TraceLEVELS.WARNING)
    m_client.run(token, bot=bot)


def get_client() -> CLIENT:
    """
    Name:   get_client
    Params: void
    Return: discord.Client | None
    Info:   Returns the client object used by the framework, so the user wouldn't have to run 2 clients.
    """
    return m_client