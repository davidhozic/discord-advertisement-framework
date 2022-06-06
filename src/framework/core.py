"""
    ~  core  ~
    This module contains the essential definitons
    and functions needed for the framework to run,
    as well as user function to control the framework
"""
from   typing import Iterable, Literal, Callable, List, Set, overload
from   _discord import Intents
from   contextlib import suppress
from . const import *
from . import tracing
from . tracing import *
from . import guild
from . import client
from . import sql
from . import message
import asyncio


#######################################################################
# Exports
#######################################################################
__all__ = (
    "run",
    "shutdown",
    "add_object",
    "remove_object"
)

#######################################################################
# Globals   (These are all set in the framework.run function)
#######################################################################
class GLOBALS:
    """ ~  GLOBALS  ~
        @Info: Contains the globally needed variables"""
    user_callback: Callable = None
    server_list: List[guild.BaseGUILD] = []
    temp_server_list: List[guild.BaseGUILD] = None # Holds the guilds that are awaiting initialization (set in framework.run and cleared after initialization)
    sql_manager: sql.LoggerSQL = None

#######################################################################
# Tasks
#######################################################################
async def advertiser(message_type: Literal["text", "voice"]) -> None:
    """
    Name  : advertiser
    Param :
        -   message_type:
            Name of the message list variable, can be t_messages for TextMESSAGE list
            and vc_messages for VoiceMESSAGE list
    Info  : Main task that is responsible for the framework
            2 tasks are created for 2 types of messages: TextMESSAGE and VoiceMESSAGE
    """
    while True:
        await asyncio.sleep(C_TASK_SLEEP_DELAY)
        for guild_user in GLOBALS.server_list: # Copy the list to prevent issues with the list being modified 
            await guild_user.advertise(message_type)


#######################################################################
# Functions
#######################################################################
async def initialize() -> bool:
    """
    Name:       initialize
    Parameters: void
    Return:     bool:
                - Returns True if ANY guild was successfully initialized
                - Returns False if ALL the guilds were not able to initialize,
                  indicating the framework should be stopped.
    Info:       Function that initializes the guild objects and
                then returns True on success or False on failure.
    """
    # Initialize the message module
    _client = client.get_client()
    await message.initialize(is_user= not _client.user.bot)
    
    # Initialize the SQL module
    sql_manager = GLOBALS.sql_manager
    if sql_manager is not None:
        if not sql.initialize(sql_manager): # Initialize the SQL database
            trace("[CORE]: Unable to initialize the SQL manager, JSON logs will be used.", TraceLEVELS.ERROR)
    else:
        trace("[CORE]: No SQL manager provided, logging will be JSON based", TraceLEVELS.WARNING)

    # Initialize the servers (and their message objects)
    trace("[CORE]: Initializing servers", TraceLEVELS.NORMAL)
    for server in GLOBALS.temp_server_list:
        await add_object(server) # Add each guild to the shilling list

    # Create advertiser tasks
    trace("[CORE]: Creating advertiser tasks", TraceLEVELS.NORMAL)
    asyncio.create_task(advertiser("text"))
    asyncio.create_task(advertiser("voice"))

    # Create the user callback task
    callback = get_user_callback()
    if callback is not None:
        trace("[CORE]: Starting user callback function", TraceLEVELS.NORMAL)
        asyncio.create_task(callback)

    del GLOBALS.sql_manager
    del GLOBALS.temp_server_list

    trace("[CORE]: Initialization complete.", TraceLEVELS.NORMAL)
    return True


@overload
async def add_object(obj: guild.BaseGUILD) -> bool: 
    """
    Name:   add_object
    Params: obj ~ guild to add to the framework
    Return: bool
    Info:   Adds an GUILD/USER to the framework"""
    ...
@overload
async def add_object(obj: message.BaseMESSAGE, guild_id: int) -> bool:
    """
    Name:   add_object
    Params: obj ~ message to add to the framework
            guild_id ~ guild id of the guild to add the message to
    Return: bool
    Info:   Adds a MESSAGE to the framework"""    
    ...
async def add_object(obj, guild_id=None) -> bool:    
    if isinstance(obj, guild.BaseGUILD):
        if obj in GLOBALS.server_list:
            trace(f"[CORE]: Guild with id: {obj.snowflake} is already in the list", TraceLEVELS.ERROR)
            return False
        if not await obj.initialize():
            return False
        GLOBALS.server_list.append(obj)
        return True
    elif isinstance(obj, message.BaseMESSAGE):
        if guild_id is None:
            trace("[CORE]: guild_id is required to add a message", TraceLEVELS.ERROR)
            return False 
        guild_user: guild.BaseGUILD # Typing hint
        for guild_user in GLOBALS.server_list:
            if guild_user.snowflake == guild_id:
                if await guild_user.add_message(obj):
                    return True
                trace(f"[CORE]: Unable to add message to guild {guild_user.apiobject}(ID: {guild_user.snowflake})", TraceLEVELS.ERROR)
                return False

        trace(f"[CORE]: Could not find guild with id: {guild_id}", TraceLEVELS.ERROR)

    return False


@overload
def remove_object(guild_id: int) -> bool: 
    """
    Name:   remove_object
    Params: guild_id ~ id of the guild to remove
    Return: None
    Info:   Removes a guild from the framework that has the given guild_id"""
    ...
@overload
def remove_object(channel_ids: Iterable) -> bool:
    """
    Name:   remove_object
    Params: channel_ids ~ set of channel ids to look for in the message 
    Return: bool
    Info:   Remove messages that containt all the given channel ids (data itearable)"""
    ...
def remove_object(data):    
    if isinstance(data, int): # Guild id
        for guild_user in GLOBALS.server_list:
            if guild_user.snowflake == data:
                GLOBALS.server_list.remove(guild_user)
                return True
    
        trace(f"[CORE]: Could not find guild with id: {data}", TraceLEVELS.WARNING)
        return False

    elif isinstance(data, Iterable):
        for guild_user in GLOBALS.server_list:
            if isinstance(guild_user, guild.GUILD): # USER doesn't have channels
                for message in guild_user.t_messages + guild_user.vc_messages:
                    msg_channels = [x.id for x in message.channels] # Generate snowflake list
                    if all(x in msg_channels for x in data): # If any of the channels in the set are in the message channel list
                        guild_user.remove_message(message) 
        return True

    return False


async def shutdown() -> None:
    """
    Name:   shutdown
    Params: void
    Return: None
    Info:   Stops the framework"""
    cl = client.get_client()
    await cl.close()


def get_user_callback() -> Callable:
    """
    Name:   get_user_callback
    Params: void
    Return: Callable
    Info:   Returns the user callback function"""
    return GLOBALS.user_callback


def run(token : str,
        server_list : list=[],
        is_user : bool =False,
        user_callback : bool=None,
        server_log_output : str ="History",
        sql_manager: sql.LoggerSQL=None,
        intents: Intents=Intents.default(),
        debug : bool=True) -> None:
    """
    @type  : function
    @name  : run
    @params:
        - token             : str       = access token for account
        - server_list       : list      = List of framework.GUILD objects
        - is_user           : bool      = Is the token from an user account
        - user_callback     : function  = Function to call on run
        - server_log_output : str       = Path where the server log files will be created
        - sql_manager       : LoggerSQL = SQL manager object that will save into the database
        - intents           : Intents   = Discord Intents object (API permissions)
        - debug             : bool      = Print trace message to the console,
                                          useful for debugging

    @description: This function is the function that starts framework and starts advertising"""
    guild.GLOBALS.server_log_path = server_log_output               # Logging folder
    tracing.m_use_debug = debug                                     # Print trace messages to the console for debugging purposes
    GLOBALS.temp_server_list = server_list                          # List of guild objects to iterate thru in the advertiser task
    GLOBALS.sql_manager = sql_manager                               # SQL manager object
    if user_callback is not None:
        GLOBALS.user_callback = user_callback()                     # Called after framework has started

    client.initialize(token, bot=not is_user, intents=intents)
