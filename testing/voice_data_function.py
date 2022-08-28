import  discron, datetime, secret
from discron import discord



############################################################################################
# It's VERY IMPORTANT that you use @framework.data_function!
############################################################################################
@discron.data_function
def get_data(param1, param2):
    return discron.AUDIO("VoiceMessage.mp3")

guilds = [
    discron.GUILD(
        guild_id=123456789,                                 # ID of server (guild)
        messages_to_send=[                                  # List MESSAGE objects 
            discron.VoiceMESSAGE(
                              start_period=None,            # If None, messages will be send on a fixed period (end period)
                              end_period=15,                # If start_period is None, it dictates the fixed sending period,
                                                            # If start period is defined, it dictates the maximum limit of randomized period
                              data=get_data(1, 2),          # Data parameter
                              channel_ids=[123456789],      # List of ids of all the channels you want this message to be sent into
                              start_now=True                # Start sending now (True) or wait until period
                              ),  
        ],
        generate_log=True           ## Generate file log of sent messages (and failed attempts) for this server 
    )
]

############################################################################################

if __name__ == "__main__":
    discron.run(  token=secret.C_TOKEN,               # MANDATORY
                    intents=discord.Intents.default(),  # OPTIONAL (see https://docs.pycord.dev/en/master/intents.html)
                    server_list=guilds,                 # MANDATORY
                    is_user=False,                      # OPTIONAL
                    user_callback=None,                 # OPTIONAL
                    server_log_output="History",        # OPTIONAL
                    debug=True)                         # OPTIONAL
    