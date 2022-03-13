"""
    DISCORD ADVERTISEMENT FRAMEWORK (DAF)
    Author      :: David Hozic
    Copyright   :: Copyright (c) 2022 David Hozic
    Version     :: V1.7.9
"""
from   typing import Literal
from . const import *
from . import tracing
from . tracing import *
from . import guild
from . import client
import asyncio




# TODO: Linting, write documentation for USER object, split into multiple modules, send method for DirectMESSAGE

if __name__ == "__main__":
    raise ImportError("This file is meant as a module and not as a script to run directly. Import it in a sepereate file and run it there")

#######################################################################
# Exports
#######################################################################
__all__ = (    # __all__ variable dictates which objects get imported when using from <module> import *
    "run",
    "shutdown"
)

#######################################################################
# Globals   (These are all set in the framework.run function)
#######################################################################
m_user_callback = None     # User provided function to call after framework is ready
m_server_list   = None        

        
#######################################################################
# Tasks
#######################################################################
async def advertiser(message_type: Literal["t_messages", "vc_messages"]) -> None:
    """
    Name  : advertiser
    Param :
        -   message_type:
            Name of the message list variable, can be t_messages for TextMESSAGE list and vc_messages for VoiceMESSAGE list
    Info  : Main task that is responsible for the framework
            2 tasks are created for 2 types of messages: TextMESSAGE and VoiceMESSAGE
    """
    while True:
        await asyncio.sleep(C_TASK_SLEEP_DELAY)
        for guild_user in m_server_list:
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
                - Returns False if ALL the guilds were not able to initialize, indicating the framework should be stopped.
    Info:       Function that initializes the guild objects and then returns True on success or False on failure.
    """
    for server in m_server_list[:]:
        if not await server.initialize():
            m_server_list.remove(server)

    if len(m_server_list):
        return True
    else:
        trace("No guilds could be parsed", TraceLEVELS.ERROR)
        return False


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
        - is_user           : bool      = Set to True if token is from an user account and not a bot account
        - user_callback     : function  = User callback function (gets called after framework is ran)
        - server_log_output : str       = Path where the server log files will be created
        - debug             : bool      = Print trace message to the console,
                                          useful for debugging if you feel like something is not working

    @description: This function is the function that starts framework and starts advertising
    """
    global m_user_callback, m_server_list

    
    guild.m_server_log_output_path = server_log_output    ## Path to folder where to crete server logs
    tracing.m_use_debug = debug                     ## Print trace messages to the console for debugging purposes
    m_server_list = server_list                     ## List of guild objects to iterate thru in the advertiser task
    m_user_callback = user_callback                 ## Called after framework has started
       
    client.initialize(token, bot=not is_user)
