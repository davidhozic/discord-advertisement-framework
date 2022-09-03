from datetime import timedelta
import  daf, datetime, secret
from daf import discord



############################################################################################
# It's VERY IMPORTANT that you use @daf.data_function!
############################################################################################
@daf.data_function
def get_data(param1, param2):
    return daf.AUDIO("VoiceMessage.mp3")


guilds = [
    daf.GUILD(
        snowflake=123456789,                                    # ID of server (guild) or a discord.Guild object or a discord.Guild object
        messages=[                                      # List MESSAGE objects 
            daf.VoiceMESSAGE(
                              start_period=None,                # If None, messages will be send on a fixed period (end period)
                              end_period=timedelta(seconds=15),                    # If start_period is None, it dictates the fixed sending period,
                                                                # If start period is defined, it dictates the maximum limit of randomized period
                              data=get_data(1, 2),              # Data parameter
                              channels=[123456789],             # List of channel ids or discord.VoiceChannel objects
                              volume=50,                        # The volume (0-100%) at which to play the audio
                              start_in=timedelta(seconds=0)                    # Start sending now (True) or wait until period
                              ),  
        ],
        logging=True           ## Generate file log of sent messages (and failed attempts) for this server 
    )
]

############################################################################################

daf.run(token=secret.C_TOKEN,        
        server_list=guilds,
        is_user=False)
    