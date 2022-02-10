import  framework, secret




############################################################################################
#                               GUILD MESSAGES DEFINITION                                  #
############################################################################################

# File object representing file that will be sent
l_file = framework.FILE("./Examples/main_send_file.py")

framework.GUILD.server_list = [
    framework.GUILD(
        guild_id=1234,            # ID of server (guild)
        messages_to_send=[        # List MESSAGE objects 
            # Will send this example file to channels every 60 seconds  
            framework.MESSAGE(start_period=None, end_period=60, data=l_file, channel_ids=[1234, 1234], clear_previous=False, start_now=True),
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
    