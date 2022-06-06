import  framework, secret
from framework import discord


some_audio_file = framework.AUDIO("VoiceMessage.mp3")

guilds = [
    framework.GUILD(
        guild_id=12345,                         # ID of server (guild)
        messages_to_send=[                      # List MESSAGE objects
            framework.VoiceMESSAGE(
                start_period=None,              # If None, messages will be send on a fixed period (end period)
                end_period=15,                  # If start_period is None, it dictates the fixed streaming period (period of channel join).,
                data=[some_audio_file],         # Data you want to send (Can be of types : AUDIO or function that returns any of above types [or returns None if you don't have any data to send yet])
                    
                channel_ids=[12345],
                start_now=True
            )  
        ],
        generate_log=True           ## Generate file log of sent messages (and failed attempts) for this server 
    )
]

############################################################################################

if __name__ == "__main__":
    framework.run(  token=secret.C_TOKEN,               # MANDATORY
                    intents=discord.Intents.default(),  # OPTIONAL (see https://docs.pycord.dev/en/master/intents.html)
                    server_list=guilds,                 # MANDATORY
                    is_user=False,                      # OPTIONAL
                    user_callback=None,                 # OPTIONAL
                    server_log_output="History",        # OPTIONAL
                    debug=True)                         # OPTIONAL