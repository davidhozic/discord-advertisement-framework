from datetime import timedelta
import  daf, datetime
from daf import discord



############################################################################################
# It's VERY IMPORTANT that you use @daf.data_function!
############################################################################################
@daf.data_function
def get_data(param1, param2):
    return daf.AUDIO("VoiceMessage.mp3")


accounts = [
    daf.ACCOUNT( # ACCOUNT 1
        "JJJKHSAJDHKJHDKJ",
        False,
        [
            daf.GUILD(123456789,
                     [        
                        daf.VoiceMESSAGE(None, timedelta(seconds=15), get_data(123), [12345, 6789]),  
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
                    daf.VoiceMESSAGE(
                                    start_period=None,                    # If None, messages will be send on a fixed period (end period)
                                    end_period=timedelta(seconds=15),       # If start_period is None, it dictates the fixed sending period,
                                                                            # If start period is defined, it dictates the maximum limit of randomized period
                                    data=get_data(1, 2), # Data you want to sent to the function (Can be of types : str, embed, file, list of types to the left
                                    channels=[12323,2313],
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