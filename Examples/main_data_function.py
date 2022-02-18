import  framework, datetime, secret




############################################################################################
#                               GUILD MESSAGES DEFINITION                                  #
############################################################################################

# It's VERY IMPORTANT that you use @framework.data_function to convert your function into a __FUNCTION_CLS__ class which creates an object when you "call" it below
#######################################


@framework.data_function
def get_data(parameter):
    l_time = datetime.datetime.now()
    return f"Parameter: {parameter}\nTimestamp: {l_time.day}.{l_time.month}.{l_time.year} :: {l_time.hour}:{l_time.minute}:{l_time.second}"

guilds = [
    framework.GUILD(
        guild_id=123456789,                                 # ID of server (guild)
        messages_to_send=[                                  # List MESSAGE objects 
            framework.MESSAGE(
                              start_period=None,            # If None, messages will be send on a fixed period (end period)
                              end_period=15,                # If start_period is None, it dictates the fixed sending period,
                                                            # If start period is defined, it dictates the maximum limit of randomized period
                              data=get_data(123),           # Data you want to sent to the function (Can be of types : str, embed, file, list of types to the left
                                                            # or function that returns any of above types(or returns None if you don't have any data to send yet), 
                                                            # where if you pass a function you need to use the framework.FUNCTION decorator on top of it ).
                              channel_ids=[123456789],      # List of ids of all the channels you want this message to be sent into
                              clear_previous=True,          # Clear all discord messages that originated from this MESSAGE object
                              start_now=True                # Start sending now (True) or wait until period
                              ),  
        ],
        generate_log=True           ## Generate file log of sent messages (and failed attempts) for this server 
    )
]

############################################################################################

if __name__ == "__main__":
    framework.run(  token=secret.C_TOKEN,           # MANDATORY,
                    server_list=guilds,             # MANDATORY
                    is_user=False,                  # OPTIONAL
                    user_callback=None,             # OPTIONAL
                    server_log_output="Logging",    # OPTIONAL
                    debug=True)                     # OPTIONAL
    