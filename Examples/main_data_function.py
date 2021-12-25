import  framework, discord, datetime




############################################################################################
#                               GUILD MESSAGES DEFINITION                                  #
############################################################################################

# Returns string containing parameter and Timestamp object(unformatted)
def get_data(parameter):
    return f"Param:{parameter}\nTimestamp: {datetime.datetime.now()}"


framework.GUILD.server_list = [
    framework.GUILD(
        guild_id=1234,                       # ID of server (guild)
        messages_to_send=[                   # List MESSAGE objects 
            ## This will call the function get_data every 60 seconds and send it parameter 12345, then it will start sending the return of that function into the channels specified by channel_ids
            framework.MESSAGE(start_period=None, end_period=60, data=(get_data, 12345), channel_ids=[1234, 1234], clear_previous=False, start_now=True), 
        ],
        generate_log=True 
    )
]
                                     
############################################################################################

if __name__ == "__main__":
    framework.run(user_callback=None)
    