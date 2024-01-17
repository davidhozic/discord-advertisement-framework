from datetime import timedelta
import  daf, datetime
from daf import discord



############################################################################################
# It's VERY IMPORTANT that you use @daf.data_function!
############################################################################################


@daf.data_function
def get_data(parameter):
    l_time = datetime.datetime.now()
    return f"Parameter: {parameter}\nTimestamp: {l_time.day}.{l_time.month}.{l_time.year} :: {l_time.hour}:{l_time.minute}:{l_time.second}"

accounts = [
    daf.ACCOUNT( # ACCOUNT 1
        "JJJKHSAJDHKJHDKJ",
        False,
        [
            daf.GUILD(123456789,
                     [        
                        daf.TextMESSAGE(None, timedelta(seconds=15), get_data(123), [12345, 6789]),  
                     ],
                     True)
        ]
    ),
    daf.ACCOUNT( # ACCOUNT 2
        token="JJJKHSAJDHKJHDKJ",
        is_user=False,
        servers=[
            daf.GUILD(
                snowflake=123456789, # ID of server (guild) or a discord.Guild object
                messages=[         # List MESSAGE objects 
                    daf.TextMESSAGE(
                                    start_period=None,                    # If None, messages will be send on a fixed period (end period)
                                    end_period=timedelta(seconds=15),       # If start_period is None, it dictates the fixed sending period,
                                                                            # If start period is defined, it dictates the maximum limit of randomized period
                                    data=get_data(123),                   # Data you want to sent to the function (Can be of types : str, embed, file, list of types to the left
                                                                            # or function that returns any of above types(or returns None if you don't have any data to send yet), 
                                                                            # where if you pass a function you need to use the daf.FUNCTION decorator on top of it ).
                                    channels=[12323,2313],
                                    mode="send",                          # "send" will send a new message every time, "edit" will edit the previous message, "clear-send" will delete
                                                                            # the previous message and then send a new one
                                    start_in=timedelta(seconds=0),        # Start sending now (True) or wait until period
                                    remove_after=None                     # Remove the message never or after n-times, after specific date or after timedelta
                                    ),  
                ],
                logging=True,       # Generate file log of sent messages (and failed attempts) for this user
                remove_after=None   # When to remove the guild and it's message from the shilling list
            )
        ]
    )
]

############################################################################################

daf.run(accounts=accounts)
