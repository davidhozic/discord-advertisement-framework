"""
    This module contains the essential definitions
    and functions needed for the framework to run,
    as well as user function to control the framework
"""
from typing import Callable, Coroutine, List, Optional, Union, overload
from contextlib import suppress
from typeguard import typechecked

from .logging.tracing import *
from .logging import sql, logging, tracing

from . import guild
from . import client
from . import misc
from . import message

import asyncio
import _discord as discord


__all__ = (
    "run",
    "shutdown",
    "add_object",
    "remove_object",
    "get_guild_user",
    "get_accounts",
    "initialize"
)


class GLOBALS:
    """
    Storage class used for holding global variables.
    """
    accounts: List[client.ACCOUNT] = []

@misc.doc_category("DAF control reference")
async def initialize(token : Optional[str]=None,
                     server_list : Optional[List[Union[guild.GUILD, guild.USER, guild.AutoGUILD]]]=None,
                     is_user : Optional[bool] =False,
                     user_callback : Optional[Union[Callable, Coroutine]]=None,
                     server_log_output : Optional[str] =None,
                     sql_manager: Optional[sql.LoggerSQL]=None,
                     intents: Optional[discord.Intents]=None,
                     debug : Optional[ Union[TraceLEVELS, int, str, bool ]] = TraceLEVELS.NORMAL,
                     proxy: Optional[str]=None,
                     logger: Optional[logging.LoggerBASE]=None,
                     accounts: Optional[List[client.ACCOUNT]]=[]) -> None:
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
    # ------------------------------------------------------------
    # Initialize tracing
    # ------------------------------------------------------------
    if isinstance(debug, bool):
        trace("Using bool for debug parameter is DEPRECATED. Use daf.logging.TraceLEVELS", TraceLEVELS.DEPRECATED)
        debug = TraceLEVELS.NORMAL if debug else TraceLEVELS.DEPRECATED
    
    tracing.initialize(debug) # Print trace messages to the console for debugging purposes
    # ------------------------------------------------------------
    # Initialize logging
    # ------------------------------------------------------------
    # --------------- DEPRECATED -------------------- #
    if server_log_output is not None:
        if logger is None:
            trace("DEPRECATED! Using this parameter is deprecated and scheduled for removal\nIt is implicitly converted to logger=LoggerJSON(path=\"History\")",
                  TraceLEVELS.DEPRECATED)
            logger = logging.LoggerJSON(path=server_log_output)
        else:
            trace("logger parameter was passed, ignoring server_log_output", TraceLEVELS.WARNING)
    
    if sql_manager is not None:
        if logger is None:
            trace("DEPRECATED! Using this parameter is deprecated and scheduled for removal\nIt is implicitly converted to logger=LoggerSQL(...)",
                  TraceLEVELS.DEPRECATED)
            logger = sql_manager
        else:
            trace("logger parameter was passed, ignoring sql_manager", TraceLEVELS.WARNING)
    # ----------------------------------------------- #
    if logger is None:
        logger = logging.LoggerJSON(path="History")

    await logging.initialize(logger)
    # ------------------------------------------------------------

    # ------------------------------------------------------------
    # Initialize accounts
    # ------------------------------------------------------------
    # ------------- DEPRECATED -----------------
    if token is not None:
        trace("Passing the token argument directly is deprecated since v2.4 where support\n"
              "for multiple accounts was added. Please use the ``accounts`` parameter", 
              TraceLEVELS.DEPRECATED)

        accounts.append(client.ACCOUNT(token=token, is_user=is_user, intents=intents, proxy=proxy, servers=server_list))
    # ------------------------------------------
    for account in accounts:
        try:
            await add_object(account)
        except Exception as exc:
            trace(f" Unable to add account.", TraceLEVELS.ERROR, exc)    

    # ------------------------------------------
    # Create the user callback task
    if user_callback is not None:
        trace("Starting user callback function", TraceLEVELS.NORMAL)
        user_callback = user_callback()
        if isinstance(user_callback, Coroutine):
            loop.create_task(user_callback)

    trace("Initialization complete.", TraceLEVELS.NORMAL)


#######################################################################
# Functions
#######################################################################

@overload
@misc.doc_category("Dynamic mod.", True)
async def add_object(obj: client.ACCOUNT) -> None:
    """
    Adds an account to the framework.

    Parameters
    ------------
    obj: client.ACCOUNT
        The account object to add
    
    Raises
    ----------
    ValueError
        The account has already been added to the list.
    TypeError
        ``obj`` is of invalid type.
    """
    ...
@overload
@misc.doc_category("Dynamic mod.", True)
async def add_object(obj: Union[guild.USER, guild.GUILD, guild.AutoGUILD], snowflake: client.ACCOUNT=None) -> None:
    """

    Adds a guild or an user to the daf.

    Parameters
    -----------
    obj: guild.USER | guild.GUILD | guild.AutoGUILD
        The guild object to add into the account (``snowflake``).
    snowflake: client.ACCOUNT=None
        The account to add this guild/user to.

    Raises
    ----------
    ValueError
        The guild/user is already added to the daf.
    TypeError
        The object provided is not supported for addition.
    TypeError
        Invalid parameter type.
    RuntimeError
        When using deprecated method of adding items to the shill list,
        no accounts were available.
    Other
        Raised in the obj.initialize() method
    """
    ...
@overload
@misc.doc_category("Dynamic mod.", True)
async def add_object(obj: Union[message.DirectMESSAGE, message.TextMESSAGE, message.VoiceMESSAGE],
                     snowflake: Union[guild.GUILD, guild.USER]) -> None:
    """
    .. deprecated:: v2.4

        Using int, discord.* objects in the snowflake parameter.
        This functionality is planned for removal in v2.5.

    Adds a message to the daf.

    Parameters
    -----------
    obj: message.DirectMESSAGE | message.TextMESSAGE | message.VoiceMESSAGE
        The message object to add into the daf.
    snowflake: guild.GUILD | guild.USER
        Which guild/user to add it to (can be snowflake id or a framework _BaseGUILD object or a discord API wrapper object).

    Raises
    ----------
    TypeError
        The object provided is not supported for addition.
    ValueError
        guild_id wasn't provided when adding a message object (to which guild should it add)
    ValueError
        Missing snowflake parameter.
    ValueError
        Could not find guild with that id.
    Other
        Raised in the obj.add_message() method
    """
    ...

async def add_object(obj, snowflake=None):
    object_type_name = type(obj).__name__

    # Add the object
    if isinstance(obj, client.ACCOUNT):
        if obj in GLOBALS.accounts:
            raise ValueError("Account already added to the list")

        await obj.initialize()
        GLOBALS.accounts.append(obj)
    elif isinstance(obj, (guild._BaseGUILD , guild.AutoGUILD)):
        if snowflake is None:
            # Compatibility with prior versions of v2.4
            trace("Directly adding guild like objects to the framework is deprecated since v2.4 (multi-account support)\n"
                  "The object will be added to the first account in the list. Update your code to pass ``snowflake`` with :class:`~daf.client.ACCOUNT`",
                  TraceLEVELS.DEPRECATED)
            try:
                snowflake = GLOBALS.accounts[0]
            except IndexError as exc:
                raise RuntimeError("No accounts are running in the framework") from exc
        
        if not isinstance(snowflake, client.ACCOUNT):
            raise TypeError("snowflake parameter type must be ACCOUNT when the obj parameter type is guild like.")

        await snowflake.add_server(obj)

    elif isinstance(obj, message.BaseMESSAGE):
        if snowflake is None:
            raise ValueError(f"snowflake parameter (guild-like) is required to add a message. Only the {object_type_name} object was provided.")
        
        if not isinstance(snowflake, (guild.AutoGUILD, guild._BaseGUILD)):
            # --------- DEPRECATED ----------- #
            # TODO: remove in v2.5, uncomment TypError            
            snowflake = get_guild_user(snowflake)
            trace("DEPRECATED! Using int or discord.* objects is deprecated for the snowflake parameter of add_object.\n"
                  "It is planned for removal in version v2.5!",
                  TraceLEVELS.DEPRECATED)
            if snowflake is None:
                raise ValueError("The GUILD/USER with specified snowflake could not be found.")
            # -------------------------------- #
            # raise TypeError("snowflake parameter must be one of: guild.AutoGUILD, guild.GUILD, guild.USER")

        await snowflake.add_message(obj)

    else:
        raise TypeError(f"Invalid object type `{object_type_name}`.")

@typechecked
@misc.doc_category("Dynamic mod.")
async def remove_object(snowflake: Union[guild._BaseGUILD, message.BaseMESSAGE, guild.AutoGUILD, client.ACCOUNT]) -> None:
    """
    .. versionchanged:: v2.4.1
        Turned async for fix bug of missing functionality

    .. versionchanged:: v2.4
        | Now accepts client.ACCOUNT.
        | Removed support for ``int`` and for API wrapper (PyCord) objects.

    Removes an object from the daf.

    Parameters
    -------------
    snowflake: guild._BaseGUILD | message.BaseMESSAGE | guild.AutoGUILD | client.ACCOUNT
        The object to remove from the framework.

    Raises
    --------------
    ValueError
        Item (with specified snowflake) not in the shilling list.
    TypeError
        Invalid argument."""    
    if isinstance(snowflake, message.BaseMESSAGE):
        for account in GLOBALS.accounts:
            for guild_ in account.servers:
                if snowflake in guild_.messages:
                    guild_.remove_message(snowflake)
                    break
        else:
            raise ValueError("Message is not in any guilds")

    elif isinstance(snowflake, (guild._BaseGUILD, guild.AutoGUILD)):
        for account in GLOBALS.accounts:
            if snowflake in account.servers:
                account.remove_server(snowflake)
    
    elif isinstance(snowflake, client.ACCOUNT):
        await snowflake._close()
        GLOBALS.accounts.remove(snowflake)


@typechecked
def get_guild_user(snowflake: Union[int, discord.Object, discord.Guild, discord.User, discord.Object]) -> Union[guild.GUILD, guild.USER, None]:
    """
    TODO: Remove in v2.5
    .. deprecated:: v2.4

    Retrieves the GUILD/USER object that has the ``snowflake`` ID from the shilling list. 

    Parameters
    -------------
    snowflake: Union[int, discord.Object, discord.Guild, discord.User, discord.Object]
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

    trace("This function is planned for removal in the future. Use ACCOUNT.get_server method instead!", TraceLEVELS.DEPRECATED)
    if isinstance(snowflake, int):
        snowflake = discord.Object(snowflake)

    for guild in GLOBALS.accounts[0]._servers:
        if guild.snowflake == snowflake.id:
            return guild

    return None


@misc.doc_category("Clients")
def get_accounts() -> List[client.ACCOUNT]:
    """
    .. versionadded:: v2.4

    Returns
    ----------
    List[client.ACCOUNT]
        List of running accounts.
    """
    return GLOBALS.accounts.copy()


@typechecked
@misc.doc_category("DAF control reference")
async def shutdown(loop: Optional[asyncio.AbstractEventLoop]=None) -> None:
    """
    Stops the framework.

    Parameters
    ----------
    loop: Optional[asyncio.AbstractEventLoop]
        The loop everything is running in.
        Leave empty for default loop.
    """
    if loop is None:
        loop = asyncio.get_event_loop()

    loop.stop()


def _shutdown_clean(loop: asyncio.AbstractEventLoop) -> None:
    """
    Signals all accounts to cleanup and then close
    connections to Discord.

    Parameters
    ---------------
    loop: asyncio.AbstractEventLoop
        The loop to stop.
    """
    for account in GLOBALS.accounts:
        loop.run_until_complete(account._close())


@typechecked
@misc.doc_category("DAF control reference")
def run(token : Optional[str]=None,
        server_list : Optional[List[Union[guild.GUILD, guild.USER, guild.AutoGUILD]]]=None,
        is_user : Optional[bool] =False,
        user_callback : Optional[Union[Callable, Coroutine]]=None,
        server_log_output : Optional[str] =None,
        sql_manager: Optional[sql.LoggerSQL]=None,
        intents: Optional[discord.Intents]=None,
        debug : Optional[ Union[TraceLEVELS, int, str, bool] ] = TraceLEVELS.NORMAL,
        proxy: Optional[str]=None,
        logger: Optional[logging.LoggerBASE]=None,
        accounts: Optional[List[client.ACCOUNT]]=[]) -> None:
    """
    Runs the framework and does not return until the framework is stopped (:func:`daf.core.shutdown`).
    After stopping, it returns None.

    .. warning::
        This will block until the framework is stopped, if you want manual control over the
        asyncio event loop, eg. you want to start the framework as a task, use
        the :func:`daf.core.initialize` coroutine.

    
    .. versionchanged:: v2.4
        Added ``accounts`` parameter.

    .. deprecated:: v2.4

        .. card::

            The following parameters were deprecated in favor of support for multiple accounts
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
            - token
            - is_user
            - server_list
            - intents
            - proxy
            +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
            The above parameters should be passed to :class:`~daf.client.ACCOUNT`.
            

    Parameters
    ---------------
    user_callback: Optional[Union[Callable, Coroutine]]
        Function or async function to call after the framework has been started.
    debug : Optional[TraceLEVELS | int | str] = TraceLEVELS.NORMAL
        .. versionchanged:: v2.3
            Deprecate use of bool (assume TraceLEVELS.NORMAL).
            Add support for TraceLEVELS or int or str that converts to TraceLEVELS.

        The level of trace for trace function to display.
        The higher value this option is, the more will be displayed.
    logger: Optional[loggers.LoggerBASE]
        The logging class to use.
        If this is not provided, JSON is automatically used.
    accounts: Optional[List[client.ACCOUNT]]
        .. versionadded:: v2.4

        List of :class:`~daf.client.ACCOUNT` (Discord accounts) to use.

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
        loop.create_task(initialize(**_params))
        loop.run_forever()
    except asyncio.CancelledError as exc:
        trace(exc, TraceLEVELS.ERROR)
    except KeyboardInterrupt:
        trace("Received a cancellation event. Stopping..", TraceLEVELS.WARNING)
    finally:
        _shutdown_clean(loop)
        asyncio.set_event_loop(None)
        loop.close()