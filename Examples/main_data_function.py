import  framework, datetime, secret




############################################################################################
#                               GUILD MESSAGES DEFINITION                                  #
############################################################################################

# VERY IMPORTANT that you use @framework.FUNCTION to convert your function into a __FUNCTION_CLS__ class which creates an object when you "call" it below
#######################################


@framework.FUNCTION
def get_data(parameter):
    return f"Parameter: {parameter}\nTimestamp: {datetime.datetime.now()}"

framework.GUILD.server_list = [
    framework.GUILD(
        guild_id=123,        ## ID of server (guild)
        messages_to_send=[                   # List MESSAGE objects 
                             ##    Period will be 5 seconds  ;  To get data, framework will call function get_data everytime before sending to discord 
            framework.MESSAGE(start_period=None, end_period=5, data=get_data(123), channel_ids=[123], clear_previous=False, start_now=True), 
        ],
        generate_log=True    ## Generate file log of sent messages (and failed attempts) for this server 
    )
]
                                     
############################################################################################

if __name__ == "__main__":
    framework.run(  token=secret.C_TOKEN,           # MANDATORY
                    is_user=False,                  # OPTIONAL
                    user_callback=None,             # OPTIONAL
                    server_log_output="Logging")    # OPTIONAL
    