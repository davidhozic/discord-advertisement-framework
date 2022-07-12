"""
    ~  core  ~
    This module contains the essential definitons
    and functions needed for the framework to run,
    as well as user function to control the framework
"""
from   typing import Any, Iterable, Literal, Callable, List, overload
from   _discord import Intents
import asyncio
import copy
import inspect
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
    "update"
)

#######################################################################
# Globals   (These are all set in the framework.run function)
#######################################################################
class GLOBALS:
    """ ~ class ~
    - @Info: Contains the globally needed variables"""
    user_callback: Callable = None
    server_list: List[guild.BaseGUILD] = []
    temp_server_list: List[guild.BaseGUILD] = None # Holds the guilds that are awaiting initialization (set in framework.run and cleared after initialization)
    sql_manager: sql.LoggerSQL = None,
    is_user: bool = False

#######################################################################
# Tasks
#######################################################################
async def advertiser(message_type: Literal["text", "voice"]) -> None:
    """ ~ coro ~
    - @Param :
        -   message_type:
            Name of the message list variable, can be t_messages for TextMESSAGE list
            and vc_messages for VoiceMESSAGE list
    @Info  : Main task that is responsible for the framework
            2 tasks are created for 2 types of messages: TextMESSAGE and VoiceMESSAGE"""
    while True:
        await asyncio.sleep(C_TASK_SLEEP_DELAY)
        for guild_user in GLOBALS.server_list: # Copy the list to prevent issues with the list being modified 
            await guild_user.advertise(message_type)


#######################################################################
# Functions
#######################################################################
async def initialize() -> None:
    """ ~ coro ~
    - @Info:      
        Function that initializes the guild objects and
        starts the shilling proccess. Also prints out any error messages that occured."""
    # Initialize the SQL module if manager is provided
    # If manager is not provided, use JSON based file logs
    sql_manager = GLOBALS.sql_manager
    if sql_manager is not None:
        if not await sql.initialize(sql_manager): # Initialize the SQL database
            trace("Unable to initialize the SQL manager, JSON logs will be used.", TraceLEVELS.WARNING)
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
    asyncio.create_task(advertiser("text"))
    asyncio.create_task(advertiser("voice"))

    # Create the user callback task
    callback = get_user_callback()
    if callback is not None:
        trace("[CORE]: Starting user callback function", TraceLEVELS.NORMAL)
        asyncio.create_task(callback)

    del GLOBALS.sql_manager         # Variable is no longer needed, instead the sql_manager inside sql.py is used
    del GLOBALS.temp_server_list    # Variable is no longer needed

    trace("[CORE]: Initialization complete.", TraceLEVELS.NORMAL)


@overload
async def add_object(obj: guild.BaseGUILD) -> None: 
    """ ~ coro ~
    - @Params: 
        - obj ~ guild to add to the framework
    - @Info:   
        - Adds an GUILD/USER to the framework
    - @Exceptions:
        - <class DAFAlreadyAddedError code=DAF_GUILD_ALREADY_ADDED> ~ Object already exits
        - <class DAFInvalidParameterError code=DAF_INVALID_TYPE>    ~ The object provided is not supported for addition."""
    ...
@overload
async def add_object(obj: message.BaseMESSAGE, guild_id: int) -> None:
    """ ~ coro ~
    - @Params: 
        - obj ~ message to add to the framework
        - guild_id ~ guild id of the guild to add the message to
    - @Info:
        - Adds a MESSAGE to the framework
    - @Exceptions:
        - <class DAFMissingParameterError code=DAF_GUILD_ID_REQUIRED> ~ guild_id wasn't provided when adding a message object (to which guild shouild it add)
        - <class DAFNotFoundError code=DAF_GUILD_ID_NOT_FOUND>        ~ Could not find guild with that id.
        - <class DAFInvalidParameterError code=DAF_INVALID_TYPE>      ~ The object provided is not supported for addition.
        """
    ...
async def add_object(obj, guild_id=None):    
    if isinstance(obj, guild.BaseGUILD):
        if obj in GLOBALS.server_list:
            raise DAFAlreadyAddedError(f"Guild with snowflake `{obj.snowflake}` is already added to the framework.", DAF_GUILD_ALREADY_ADDED)

        await obj.initialize()
        GLOBALS.server_list.append(obj)

    elif isinstance(obj, message.BaseMESSAGE):
        if guild_id is None:
            raise DAFMissingParameterError("`guild_id` is required to add a message. Only the xMESSAGE object was provided.", DAF_GUILD_ID_REQUIRED)

        for guild_user in GLOBALS.server_list:
            if guild_user.snowflake == guild_id:
                await guild_user.add_message(obj)
                return

        raise DAFNotFoundError(f"Guild with snowflake `{guild_id}` was not found in the framework.", DAF_GUILD_ID_NOT_FOUND)
    
    else:
        raise DAFInvalidParameterError(f"Invalid object type `{type(obj)}`.", DAF_INVALID_TYPE)


@overload
def remove_object(guild_id: int) -> None: 
    """
    - @Info:   Removes a guild from the framework that has the given guild_id
    - @Param: guild_id ~ id of the guild to remove
    - @Exceptions:
        - <class DAFNotFoundError code=DAF_GUILD_ID_NOT_FOUND> ~ Could not find guild with that id.
        - <class DAFInvalidParameterError code=DAF_INVALID_TYPE> ~ The object provided is not supported for removal."""
    ...
@overload
def remove_object(channel_ids: Iterable) -> None:
    """
    - @Info:   Remove messages that containt all the given channel ids (data itearable)
    - @Param: channel_ids ~ set of channel ids to look for in the message
    - @Exceptions:
        - <class DAFInvalidParameterError code=DAF_INVALID_TYPE> ~ The object provided is not supported for removal."""
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
        raise DAFInvalidParameterError(f"Invalid parameter type `{type(data)}`.", DAF_INVALID_TYPE)


async def update(object_: Any, *, init_options: dict = {},**kwargs):
        """ ~ async method ~
        - @Added in v1.9.5
        - @Info:
            Used for chaning the initialization parameters the object was initialized with.
        - @Params:
            - The allowed parameters are the initialization parameters first used on creation of the object AND 
            - init_options ~ Contains the initialization options used in .initialize() method for reainitializing certain objects.
                             This is implementation specific and not necessarily available.
        - @Exception:
            - <class DAFInvalidParameterError code=DAF_UPDATE_PARAMETER_ERROR> ~ Invalid keyword argument was passed
            - Other exceptions raised from .initialize() method"""
        
        init_keys = inspect.getfullargspec(object_.__init__).args # Retrievies list of call args
        init_keys.remove("self")
        current_state = copy.copy(object_) # Make a copy of the current object for restoration in case of update failure
        try:  
            for k in kwargs:
                if k not in init_keys:
                    raise DAFInvalidParameterError(f"Keyword argument `{k}` was passed which is not allowed. The update method only accepts the following keyword arguments: {init_keys}", DAF_UPDATE_PARAMETER_ERROR)
            # Most of the variables inside the object have the same names as in the __init__ function.
            # This section stores attributes, that are the same, into the `updated_params` dictionary and
            # then calls the __init__ method with the same parameters, with the exception of start_period, end_period and start_now parameters
            updated_params = {}
            for k in init_keys:
                # Store the attributes that match the __init__ parameters into `updated_params`
                updated_params[k] = kwargs[k] if k in kwargs else getattr(object_, k)

            # Call the implementation __init__ function and then initialize API related things
            object_.__init__(**updated_params)
            # Call additional initialization function (if it has one)
            if hasattr(object_, "initialize"):
                await object_.initialize(**init_options)
        except Exception:
            # In case of failure, restore to original attributes
            for k in type(object_).__slots__:
                setattr(object_, k, getattr(current_state, k))
            raise


async def shutdown() -> None:
    """ ~ coro ~
    - @ Info: Stops the framework"""
    cl = client.get_client()
    await cl.close()


def get_user_callback() -> Callable:
    """ ~ function ~
    - @Return: Callable
    - @Info:   Returns the user callback function"""
    return GLOBALS.user_callback


def run(token : str,
        server_list : list=[],
        is_user : bool =False,
        user_callback : bool=None,
        server_log_output : str ="History",
        sql_manager: sql.LoggerSQL=None,
        intents: Intents=Intents.default(),
        debug : bool=True) -> None:
    """ ~ function ~
    - @Param:
        - token             ~ access token for account
        - server_list       ~ List of framework.GUILD objects
        - is_user           ~ Is the token from an user account
        - user_callback     ~ Function to call on run
        - server_log_output ~ Path where the server log files will be created
        - sql_manager       ~ SQL manager object that will save into the database
        - intents           ~ Discord Intents object (API permissions)
        - debug             ~ Print trace message to the console, useful for debugging
    - @Info: This function is the function that starts framework and starts advertising"""
    guild.GLOBALS.server_log_path = server_log_output               # Logging folder
    tracing.m_use_debug = debug                                     # Print trace messages to the console for debugging purposes
    GLOBALS.temp_server_list = server_list                          # List of guild objects to iterate thru in the advertiser task
    GLOBALS.sql_manager = sql_manager                               # SQL manager object
    GLOBALS.is_user = is_user                                       # Is the token from an user account
    if user_callback is not None:
        GLOBALS.user_callback = user_callback()                     # Called after framework has started

    client.initialize(token, bot=not is_user, intents=intents)
