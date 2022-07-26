"""
    This module contains the essential definitions
    and functions needed for the framework to run,
    as well as user function to control the framework
"""
from   typing import Any, Dict, Iterable, Literal, Callable, List, Optional, Union, overload
import asyncio
import copy
import inspect
import _discord as dc
from . const import *
from . exceptions import *
from . import tracing
from . tracing import *
from . import guild
from . import client
from . import sql
from . import message


#######################################################################
# Exports
#######################################################################
__all__ = (
    "run",
    "shutdown",
    "add_object",
    "remove_object",
)

#######################################################################
# Globals   (These are all set in the framework.run function)
#######################################################################
class GLOBALS:
    """
    Storage class used for holding global variables.
    """
    user_callback: Callable = None
    server_list: List[guild._BaseGUILD] = []
    temp_server_list: List[guild._BaseGUILD] = None # Holds the guilds that are awaiting initialization (set in framework.run and cleared after initialization)
    sql_manager: sql.LoggerSQL = None,
    is_user: bool = False


#######################################################################
# Tasks
#######################################################################
async def _advertiser(message_type: Literal["text", "voice"]) -> None:
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
            await guild_user.advertise(message_type)


#######################################################################
# Functions
#######################################################################
async def _initialize() -> None:
    """
    The main initialization function.
    It initializes all the other modules, creates advertising tasks
    and initializes all the core functionality.
    """
    # Initialize the SQL module if manager is provided
    # If manager is not provided, use JSON based file logs
    sql_manager = GLOBALS.sql_manager
    _client = client.get_client()
    if sql_manager is not None:
        try:
            await sql.initialize(sql_manager) # Initialize the SQL database
        except DAFSQLError as ex:
            trace(f"Unable to initialize the SQL manager, JSON logs will be used.\nReason: {ex}", TraceLEVELS.WARNING)
    else:
        trace("[CORE]: No SQL manager provided, logging will be JSON based", TraceLEVELS.NORMAL)

    # Initialize the servers (and their message objects)
    trace("[CORE]: Initializing servers", TraceLEVELS.NORMAL)
    for server in GLOBALS.temp_server_list:
        try:
            await add_object(server) # Add each guild to the shilling list
        except DAFError as ex:
            trace(ex)

    # Create advertiser tasks
    trace("[CORE]: Creating advertiser tasks", TraceLEVELS.NORMAL)
    _client.loop.create_task(_advertiser("text"))
    _client.loop.create_task(_advertiser("voice"))

    # Create the user callback task
    callback = get_user_callback()
    if callback is not None:
        trace("[CORE]: Starting user callback function", TraceLEVELS.NORMAL)
        _client.loop.create_task(callback)

    del GLOBALS.sql_manager         # Variable is no longer needed, instead the sql_manager inside sql.py is used
    del GLOBALS.temp_server_list    # Variable is no longer needed

    trace("[CORE]: Initialization complete.", TraceLEVELS.NORMAL)


@overload
async def add_object(obj: Union[guild.USER, guild.GUILD]) -> None: 
    """

    Adds a guild or an user to the framework.
    
    Parameters
    --------------
    obj: Union[guild.USER, guild.GUILD]
        The guild object to add into the framework.

    Raises
    -----------
    DAFParameterError(code=DAF_GUILD_ALREADY_ADDED)
         The guild/user is already added to the framework.
    DAFParameterError(code=DAF_INVALID_TYPE)
         The object provided is not supported for addition.
    Other
        Raised in the obj.initialize() method
    """
    ...
@overload
async def add_object(obj: Union[message.DirectMESSAGE, message.TextMESSAGE, message.VoiceMESSAGE],
                     snowflake: Union[int, guild.GUILD, guild.USER, dc.Guild, dc.User]) -> None:
    """

    Adds a message to the framework.
    
    Parameters
    --------------
    obj: Union[message.DirectMESSAGE, message.TextMESSAGE, message.VoiceMESSAGE]
        The message object to add into the framework.
    snowflake: Union[int, guild.GUILD, guild.USER, dc.Guild, dc.User]
        Which guild/user to add it to (can be snowflake id or a framework _BaseGUILD object or a discord API wrapper object).

    Raises
    -----------
    DAFParameterError(code=DAF_GUILD_ID_REQUIRED)
         guild_id wasn't provided when adding a message object (to which guild should it add)
    DAFNotFoundError(code=DAF_GUILD_ID_NOT_FOUND)
        Could not find guild with that id.
    DAFParameterError(code=DAF_INVALID_TYPE)
         The object provided is not supported for addition.
    Other
        Raised in the obj.add_message() method
    """
    ...
async def add_object(obj, snowflake=None):
    object_type_name = type(obj).__name__
    # Convert the `snowflake` object into a discord snowflake ID (only if adding a message to guild)
    if isinstance(snowflake, (dc.Guild, dc.User)):
        snowflake = snowflake.id
    elif isinstance(snowflake, guild._BaseGUILD):
        snowflake = snowflake.snowflake

    # Add the object
    if isinstance(obj, guild._BaseGUILD):
        if obj in GLOBALS.server_list:
            raise DAFParameterError(f"{object_type_name} with snowflake `{obj.snowflake}` is already added to the framework.", DAF_GUILD_ALREADY_ADDED)

        await obj.initialize()
        GLOBALS.server_list.append(obj)

    elif isinstance(obj, message.BaseMESSAGE):
        if snowflake is None:
            raise DAFParameterError(f"`snowflake` is required to add a message. Only the {object_type_name} object was provided.", DAF_GUILD_ID_REQUIRED)

        for guild_user in GLOBALS.server_list:
            if guild_user.snowflake == snowflake:
                await guild_user.add_message(obj)
                return

        raise DAFNotFoundError(f"Guild or user with snowflake `{snowflake}` was not found in the framework.", DAF_GUILD_ID_NOT_FOUND)

    else:
        raise DAFParameterError(f"Invalid object type `{object_type_name}`.", DAF_INVALID_TYPE)


@overload
def remove_object(guild_id: int) -> None: 
    """
    Removes a guild from the framework that has the given guild_id.
    
    Parameters
    -------------
    - guild_id: `int` - ID of the guild to remove.
    
    Raises
    --------------
    DAFNotFoundError(code=DAF_GUILD_ID_NOT_FOUND)
         Could not find guild with that id.
    DAFParameterError(code=DAF_INVALID_TYPE)
         The object provided is not supported for removal."""
    ...
@overload
def remove_object(channel_ids: Iterable[int]) -> None:
    """
    Removes messages that contain all the given channel ids.
    
    Parameters
    --------------
    channel_ids: Iterable
        The channel IDs that the message must have to be removed (it must have all of these).
    
    Raises
    --------------------
    DAFParameterError(code=DAF_INVALID_TYPE)
        The object provided is not supported for removal.
    """
    ...
def remove_object(data):    
    if isinstance(data, int): # Guild id
        for guild_user in GLOBALS.server_list:
            if guild_user.snowflake == data:
                GLOBALS.server_list.remove(guild_user)
                return
        raise DAFNotFoundError(f"Guild with snowflake `{data}` was not found in the framework.", DAF_GUILD_ID_NOT_FOUND)

    elif isinstance(data, Iterable): # Channel ids
        for guild_user in GLOBALS.server_list:
            if isinstance(guild_user, guild.GUILD): # USER doesn't have channels
                for message in guild_user.t_messages + guild_user.vc_messages:
                    msg_channels = [x.id for x in message.channels] # Generate snowflake list
                    if all(x in msg_channels for x in data): # If any of the channels in the set are in the message channel list
                        guild_user.remove_message(message)
    else:
        raise DAFParameterError(f"Invalid parameter type `{type(data)}`.", DAF_INVALID_TYPE)


async def _update(obj: Any, *, init_options: dict = {}, **kwargs):
        """
        .. versionadded:: v2.0

        Used for changing the initialization parameters the obj was initialized with.
        
        .. warning::
            Upon updating, the internal state of objects get's reset, meaning you basically have a brand new created object.   

        .. warning::
            This is not meant for manual use, but should be used only by the obj's method.

        Parameters
        -------------
        obj: Any
            The object that contains a .update() method.
        init_options: dict
            Contains the initialization options used in .initialize() method for re-initializing certain objects.
            This is implementation specific and not necessarily available.
        Other:
            Other allowed parameters are the initialization parameters first used on creation of the object.

        Raises
        ------------
        DAFParameterError(code=DAF_UPDATE_PARAMETER_ERROR)
            Invalid keyword argument was passed.
        Other
            Raised from .initialize() method.
        """
        init_keys = inspect.getfullargspec(obj.__init__).args # Retrieves list of call args
        init_keys.remove("self")
        current_state = copy.copy(obj) # Make a copy of the current object for restoration in case of update failure
        try:  
            for k in kwargs:
                if k not in init_keys:
                    raise DAFParameterError(f"Keyword argument `{k}` was passed which is not allowed. The update method only accepts the following keyword arguments: {init_keys}", DAF_UPDATE_PARAMETER_ERROR)
            # Most of the variables inside the object have the same names as in the __init__ function.
            # This section stores attributes, that are the same, into the `updated_params` dictionary and
            # then calls the __init__ method with the same parameters, with the exception of start_period, end_period and start_now parameters
            updated_params = {}
            for k in init_keys:
                # Store the attributes that match the __init__ parameters into `updated_params`
                updated_params[k] = kwargs[k] if k in kwargs else getattr(obj, k)

            # Call the implementation __init__ function and then initialize API related things
            obj.__init__(**updated_params)
            # Call additional initialization function (if it has one)
            if hasattr(obj, "initialize"):
                await obj.initialize(**init_options)
        
        except Exception:
            # In case of failure, restore to original attributes
            for k in type(obj).__slots__:
                setattr(obj, k, getattr(current_state, k))

            raise


async def shutdown() -> None:
    """
    Stops the framework and any user tasks.
    """
    cl = client.get_client()
    await cl.close()


def get_user_callback() -> Callable:
    """
    Returns the user coroutine.
    """
    return GLOBALS.user_callback


def run(token : str,
        server_list : Optional[List[Union[guild.GUILD, guild.USER]]]=[],
        is_user : Optional[bool] =False,
        user_callback : Optional[Callable]=None,
        server_log_output : Optional[str] ="History",
        sql_manager: Optional[sql.LoggerSQL]=None,
        intents: Optional[dc.Intents]=dc.Intents.default(),
        debug : Optional[bool]=True) -> None:
    """
    Runs the framework. 

    This is the very first thing that needs to be called to start the framework.
    
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
    """

    guild.GLOBALS.server_log_path = server_log_output               # Logging folder
    GLOBALS.temp_server_list = server_list                          # List of guild objects to iterate thru in the advertiser task
    GLOBALS.sql_manager = sql_manager                               # SQL manager object
    GLOBALS.is_user = is_user                                       # Is the token from an user account
    if user_callback is not None:
        GLOBALS.user_callback = user_callback()                     # Called after framework has started
    
    tracing.initialize(debug)                                       # Print trace messages to the console for debugging purposes
    client._initialize(token, bot=not is_user, intents=intents)
