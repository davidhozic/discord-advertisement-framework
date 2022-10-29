import  daf, secret
from daf import discord
from datetime import timedelta


############################################################################################
#                               GUILD MESSAGES DEFINITION                                  #
############################################################################################

# File object representing file that will be sent
l_file = daf.FILE("./Examples/main_send_file.py")

guilds = [
    daf.GUILD(
        snowflake=123456789,    # ID of server (guild) or a discord.Guild object
        messages=[              # List MESSAGE objects
            daf.TextMESSAGE(
                              start_period=None,                # If None, messages will be send on a fixed period (end period)
                              end_period=timedelta(seconds=15), # If start_period is None, it dictates the fixed sending period,
                                                                # If start period is defined, it dictates the maximum limit of randomized period
                              data=l_file,                      # Data you want to sent to the function (Can be of types : str, embed, file, list of types to the left
                                                                # or function that returns any of above types(or returns None if you don't have any data to send yet), 
                                                                # where if you pass a function you need to use the daf.FUNCTION decorator on top of it ).
                              channels=[123456789],             # List of ids of all the channels you want this message to be sent into
                              mode="send",                      # "send" will send a new message every time, "edit" will edit the previous message, "clear-send" will delete
                                                                # the previous message and then send a new one
                              start_in=timedelta(seconds=0),    # Start sending now (True) or wait until period
                              remove_after=None                 # Remove the message never or after n-times, after specific date or after timedelta
                              ),  
        ],
        logging=True,           # Generate file log of sent messages (and failed attempts) for this server 
        remove_after=None       # When to remove the guild and it's message from the shilling list
    )
]
                                     
############################################################################################

daf.run(token=secret.C_TOKEN,        
        server_list=guilds,
        is_user=False)
    