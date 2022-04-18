"""
    ~  core  ~
    This module contains the essential definitons
    and functions needed for the framework to run,
    as well as user function to control the framework
"""
from   typing import Literal, Callable, List
from . const import *
from . import tracing
from . tracing import *
from . import guild
from . import client
import asyncio


#######################################################################
# Exports
#######################################################################
__all__ = (
    "run",
    "shutdown"
)


#######################################################################
# Globals   (These are all set in the framework.run function)
#######################################################################
class GLOBALS:
    """ ~  GLOBALS  ~
        @Info: Contains the globally needed variables"""
    user_callback: Callable
    server_list: List


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
        for guild_user in GLOBALS.server_list:
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
    for server in GLOBALS.server_list[:]:
        if not await server.initialize():
            GLOBALS.server_list.remove(server)

    if not len(GLOBALS.server_list):
        trace("No guilds could be parsed", TraceLEVELS.ERROR)
        return False

    return True


async def shutdown() -> None:
    """
    Name:   shutdown
    Params: void
    Return: None
    Info:   Stops the framework
    """
    cl = client.get_client()
    await cl.close()


def run(token : str,
        server_list : list,
        is_user : bool =False,
        user_callback : bool=None,
        server_log_output : str ="History",
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
        - debug             : bool      = Print trace message to the console,
                                          useful for debugging

    @description: This function is the function that starts framework and starts advertising
    """

    guild.GLOBALS.server_log_path = server_log_output       ## Logging folder
    tracing.m_use_debug = debug                             ## Print trace messages to the console for debugging purposes
    GLOBALS.server_list = server_list                       ## List of guild objects to iterate thru in the advertiser task
    GLOBALS.user_callback = user_callback                   ## Called after framework has started

    client.initialize(token, bot=not is_user)
