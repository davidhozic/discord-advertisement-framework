from datetime import timedelta
import  daf

guilds = [
    daf.GUILD(
        snowflake=123456789,    # ID of server (guild) or a discord.Guild object
        messages=[              # List MESSAGE objects
            daf.TextMESSAGE(
                              start_period=None,                # If None, messages will be send on a fixed period (end period)
                              end_period=timedelta(seconds=15), # If start_period is None, it dictates the fixed sending period,
                                                                # If start period is defined, it dictates the maximum limit of randomized period
                              data="First message",             # Data you want to sent to the function (Can be of types : str, embed, file, list of types to the left
                                                                # or function that returns any of above types(or returns None if you don't have any data to send yet), 
                                                                # where if you pass a function you need to use the daf.FUNCTION decorator on top of it ).
                              channels=[123456789],             # List of ids of all the channels you want this message to be sent into or discord channel Objects
                              mode="send",                      # "send" will send a new message every time, "edit" will edit the previous message, "clear-send" will delete
                                                                # the previous message and then send a new one
                              start_in=timedelta(seconds=0),    # Delay before shilling start
                              remove_after=None                 # Remove after never (None)
                              ),
            daf.TextMESSAGE(start_period=5, end_period=timedelta(10), data="Second Message", channels=[12345], mode="send", start_in=timedelta(seconds=0))  
        ],
        logging=True,           # Generate file log of sent messages (and failed attempts) for this server 
        remove_after=None       # Never stop shilling to this guild
    )
]
                                     
############################################################################################

daf.run(
        token="DNASNDANDASKJNDAKSJDNASKJDNASKJNSDSAKDNAKLSNDSKAJDN",        
        is_user=False,
        server_list=guilds,
    )