"""
    This module contains the essential definitions
    and functions needed for the framework to run,
    as well as user function to control the framework
"""
from typing import (Callable, List, Optional, Union, overload)
from typeguard import typechecked

from .common import *
from .exceptions import *
from .import tracing
from .tracing import *

from . import guild
from . import client
from . import sql
from . import message
from . import misc

import asyncio
import _discord as dc

#######################################################################
# Exports
#######################################################################
__all__ = (
    "run",
    "shutdown",
    "add_object",
    "remove_object",
    "get_guild_user"
)

#######################################################################
# Globals   (These are all set in the daf.run function)
#######################################################################
class GLOBALS:
    """
    Storage class used for holding global variables.
    """
    server_list: List[guild._BaseGUILD] = []


#######################################################################
# Coroutines
#######################################################################
async def _advertiser(message_type: AdvertiseTaskType) -> None:
    """
    The task that is responsible for shilling to channels.
    This is the most top level task.

    Parameters
    ------------
    message_type: str
        Two tasks advertising tasks are created, this variable tells the guild objects which
        task is requesting to shill, so it knows what type of messages to actually send.
    """
    while True:
        await asyncio.sleep(C_TASK_SLEEP_DELAY)
        for guild_user in GLOBALS.server_list[:]: # Shallow copy list to allow dynamic removal and addition of objects
            await guild_user._advertise(message_type)


async def _initialize(token : str,
                      server_list : Optional[List[Union[guild.GUILD, guild.USER]]]=[],
                      is_user : Optional[bool] =False,
                      user_callback : Optional[Callable]=None,
                      server_log_output : Optional[str] ="History",
                      sql_manager: Optional[sql.LoggerSQL]=None,
                      intents: Optional[dc.Intents]=None,
                      debug : Optional[bool]=True,
                      proxy: Optional[str]=None) -> None:
    """
    The main initialization function.
    It initializes all the other modules, creates advertising tasks
    and initializes all the core functionality.
    If you want to control your own event loop, use this instead of run.

    Parameters
    ---------------
    Any: Any
        Parameters are the same as in :func:`daf.core.run`.
    """
    loop = asyncio.get_event_loop()
    tracing.initialize(debug) # Print trace messages to the console for debugging purposes
    
    if intents is None: # Sphinx doesn't like if this is directly in the declaration
        intents = dc.Intents.default()

    # Initialize discord client
    trace("[CORE:] Logging in...")
    await client._initialize(token, bot=not is_user, intents=intents, proxy=proxy)

    # Initialize guild
    await guild._initialize(server_log_output)

    # Initialize the servers (and their message objects)
    trace("[CORE]: Initializing servers", TraceLEVELS.NORMAL)
    for server in server_list:
        try:
            await add_object(server) # Add each guild to the shilling list
        except (DAFError, ValueError, TypeError) as ex:
            trace(ex)
    
    # Initialize SQL module
    if not await sql.initialize(sql_manager):
        trace("[CORE:] JSON based file logging will be used")

    # Create advertiser tasks
    trace("[CORE]: Creating advertiser tasks", TraceLEVELS.NORMAL)
    loop.create_task(_advertiser(AdvertiseTaskType.TEXT_ISH))
    loop.create_task(_advertiser(AdvertiseTaskType.VOICE))

    # Create the user callback task
    if user_callback is not None:
        trace("[CORE]: Starting user callback function", TraceLEVELS.NORMAL)
        loop.create_task(user_callback())

    trace("[CORE]: Initialization complete.", TraceLEVELS.NORMAL)


#######################################################################
# Functions
#######################################################################

@overload
async def add_object(obj: Union[guild.USER, guild.GUILD]) -> None:
    """

    Adds a guild or an user to the daf.

    Parameters
    --------------
    obj: Union[guild.USER, guild.GUILD]
        The guild object to add into the daf.

    Raises
    -----------
    ValueError
         The guild/user is already added to the daf.
    TypeError
         The object provided is not supported for addition.
    TypeError
        Invalid parameter type.
    Other
        Raised in the obj.initialize() method
    """
    ...
@overload
async def add_object(obj: Union[message.DirectMESSAGE, message.TextMESSAGE, message.VoiceMESSAGE],
                     snowflake: Union[int, guild.GUILD, guild.USER, dc.Guild, dc.User, dc.Object]) -> None:
    """

    Adds a message to the daf.

    Parameters
    --------------
    obj: Union[message.DirectMESSAGE, message.TextMESSAGE, message.VoiceMESSAGE]
        The message object to add into the daf.
    snowflake: Union[int, guild.GUILD, guild.USER, dc.Guild, dc.User]
        Which guild/user to add it to (can be snowflake id or a framework _BaseGUILD object or a discord API wrapper object).

    Raises
    -----------
    ValueError
        guild_id wasn't provided when adding a message object (to which guild should it add)
    TypeError
        The object provided is not supported for addition.
    TypeError
        Missing snowflake parameter.
    DAFNotFoundError(code=DAF_SNOWFLAKE_NOT_FOUND)
        Could not find guild with that id.
    Other
        Raised in the obj.add_message() method
    """
    ...
async def add_object(obj, snowflake=None):
    object_type_name = type(obj).__name__
    # Convert the `snowflake` object into a discord snowflake ID (only if adding a message to guild)
    if isinstance(snowflake, (dc.Guild, dc.User, dc.Object)):
        snowflake = snowflake.id
    elif isinstance(snowflake, guild._BaseGUILD):
        snowflake = snowflake.snowflake

    # Add the object
    if isinstance(obj, guild._BaseGUILD):
        if obj in GLOBALS.server_list:
            raise ValueError(f"{object_type_name} with snowflake `{obj.snowflake}` is already added to the daf.")

        await obj.initialize()
        GLOBALS.server_list.append(obj)

    elif isinstance(obj, message.BaseMESSAGE):
        if snowflake is None:
            raise TypeError(f"`snowflake` is required to add a message. Only the {object_type_name} object was provided.")

        for guild_user in GLOBALS.server_list:
            if guild_user.snowflake == snowflake:
                await guild_user.add_message(obj)
                return

        raise DAFNotFoundError(f"Guild or user with snowflake `{snowflake}` was not found in the daf.", DAF_SNOWFLAKE_NOT_FOUND)

    else:
        raise TypeError(f"Invalid object type `{object_type_name}`.")


def remove_object(snowflake: Union[int, dc.Object, dc.Guild, dc.User, dc.Object, guild._BaseGUILD, message.BaseMESSAGE]) -> None:
    """
    Removes an object from the daf.

    Parameters
    -------------
    snowflake: Union[int, dc.Object, dc.Guild, dc.User, dc.Object, guild.GUILD, guild.USER , message.TextMESSAGE, message.VoiceMESSAGE, message.DirectMESSAGE]
        The GUILD/USER object to remove/snowflake of GUILD/USER
        or a xMESSAGE object

    Raises
    --------------
    DAFNotFoundError(code=DAF_SNOWFLAKE_NOT_FOUND)
         Could not find guild with that id.
    TypeError
        Invalid argument."""    
    if isinstance(snowflake, message.BaseMESSAGE):
        for _guild in GLOBALS.server_list:
            if snowflake in _guild.messages:
                _guild.remove_message(snowflake)
        return

    if isinstance(snowflake, int):
        snowflake = dc.Object(snowflake)

    if not isinstance(snowflake, guild._BaseGUILD):
        snowflake = get_guild_user(snowflake)

    if snowflake is not None and snowflake in GLOBALS.server_list:
        GLOBALS.server_list.remove(snowflake)
    else:
        raise DAFNotFoundError(f"GUILD/USER not in the shilling list.", DAF_SNOWFLAKE_NOT_FOUND)


def get_guild_user(snowflake: Union[int, dc.Object, dc.Guild, dc.User, dc.Object]) -> Union[guild.GUILD, guild.USER, None]:
    """
    Retrieves the GUILD/USER object that has the ``snowflake`` ID from the shilling list. 

    Parameters
    -------------
    snowflake: Union[int, dc.Object, dc.Guild, dc.User, dc.Object]
        Snowflake ID or discord objects containing snowflake id of the GUILD.
    
    Raises
    ---------------
    TypeError
        Incorrect snowflake type

    Returns
    ---------------
    :class:`daf.guild.GUILD` | :class:`daf.guild.USER`
        The object requested.
    None
        If not guild/user not in the shilling list.
    """
    if isinstance(snowflake, int):
        snowflake = dc.Object(snowflake)

    for guild in GLOBALS.server_list:
        if guild.snowflake == snowflake.id:
            return guild

    return None


def shutdown(loop: Optional[asyncio.AbstractEventLoop]=None) -> None:
    """
    Stops the framework and any user tasks.

    .. versionchanged:: v2.1
        Made the function non async and shutdown everything.

    Parameters
    ----------
    loop: Optional[asyncio.AbstractEventLoop]
        The loop everything is running in.
        Leave empty for default loop.
    """
    if loop is None:
        loop = asyncio.get_event_loop()

    # Shutdown discord
    cl = client.get_client()
    loop.run_until_complete(cl.close()) 
    # Cancell all tasks
    tasks = [task for task in asyncio.all_tasks(loop) if not task.done()]
    for task in tasks:
        task.cancel()

    loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
    loop.run_until_complete(loop.shutdown_asyncgens())
    loop.run_until_complete(loop.shutdown_default_executor())
    loop.close()


def get_shill_list() -> List[Union[guild.GUILD, guild.USER]]:
    """
    .. versionadded:: v2.1

    Returns
    -----------
    List[Union[guild.GUILD, guild.USER]]
        The shilling list.
    """
    return GLOBALS.server_list.copy()


@typechecked
def run(token : str,
        server_list : Optional[List[Union[guild.GUILD, guild.USER]]]=[],
        is_user : Optional[bool] =False,
        user_callback : Optional[Callable]=None,
        server_log_output : Optional[str] ="History",
        sql_manager: Optional[sql.LoggerSQL]=None,
        intents: Optional[dc.Intents]=None,
        debug : Optional[bool]=True,
        proxy: Optional[str]=None) -> None:
    """
    Runs the framework and does not return until the framework is stopped (:func:`daf.core.shutdown`).
    After stopping, it returns None.

    .. versionchanged:: v2.1
        Added ``proxy`` parameter

    Parameters
    ---------------
    token: str
        Discord's access token for account.
    server_list: Optional[List[Union[:ref:`GUILD`, :ref:`USER`]]
        Predefined server list (guild list) to shill.
    is_user: Optional[bool]
        Set to True if the token is for an user account.
    user_callback: Optional[Callable]
        Users coroutine (task) to run after the framework is run.
    server_log_output: Optional[str]
        Path where the server log files will be created.
    sql_manager: Optional[:ref:`LoggerSQL`]
        SQL manager object that will save logs into the database.
    intents: Optional[discord.Intents]
        Discord Intents object (represents settings to which events it will be listened to).
    debug: Optional[bool]
        Print trace message to the console, useful for debugging.
    proxy: Optional[str]
        URL of a proxy you want the framework to use.

    Raises
    ---------------
    ModuleNotFoundError
        Missing modules for the wanted functionality, install with ``pip install discord-advert-framework[optional-group]``.
    
    ValueError
        Invalid proxy url.
    """
    _params = locals().copy()
    loop = asyncio.get_event_loop()
    try:
        loop.create_task(_initialize(**_params))
        loop.run_forever()
    except asyncio.CancelledError as exc:
        trace(exc, TraceLEVELS.ERROR)
    except KeyboardInterrupt:
        trace("Received a cancellation event. Stopping..", TraceLEVELS.WARNING)
    finally:
        shutdown(loop)