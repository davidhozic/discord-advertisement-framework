import  framework, datetime




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
        guild_id=863071397207212052,        # ID of server (guild)
        messages_to_send=[                   # List MESSAGE objects 
                             #    Period will be 5 seconds  ;  To get data, framework will call function get_data everytime before sending to discord 
            framework.MESSAGE(start_period=None, end_period=5, data=get_data(123), channel_ids=[863071397207212056], clear_previous=False, start_now=True), 
        ],
        generate_log=True 
    )
]
                                     
############################################################################################

if __name__ == "__main__":
    framework.run(user_callback=None)
    