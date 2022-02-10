import  framework, secret




############################################################################################
#                               GUILD MESSAGES DEFINITION                                  #
############################################################################################

framework.GUILD.server_list = [
    framework.GUILD(
        guild_id=1234,               # ID of server (guild)
        messages_to_send=[                   # List MESSAGE objects 
            framework.MESSAGE(start_period=None, end_period=60, data="First message", channel_ids=[1234, 1234], clear_previous=False, start_now=True),  ## Will sent a message every 60 seconds
            framework.MESSAGE(start_period=30, end_period=60, data="Second message", channel_ids=[1234, 1234], clear_previous=False, start_now=True) ## Will sent a message every period between 30 and 60 seconds (randomly chosen)
        ],
        generate_log=True 
    )
]
                                     
############################################################################################

if __name__ == "__main__":
    framework.run(  token=secret.C_TOKEN,           # MANDATORY
                    is_user=False,                  # OPTIONAL
                    user_callback=None,             # OPTIONAL
                    server_log_output="Logging")    # OPTIONAL