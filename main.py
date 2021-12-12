import  framework


############################################################################################
#                               GUILD MESSAGES DEFINITION                                  #
############################################################################################

# MESSAGE parameters: start_period , end_period , data, channel_ids , clear_previous , start_now)

# EXAMPLE:

framework.GUILD.server_list = [
    framework.GUILD(
        123456789,       # ID of server (guild)
        [                # List MESSAGE objects 
            framework.MESSAGE(start_period=None, end_period=0, data="", channel_ids=[123456789, 123456789], clear_previous=False, start_now=True),
            framework.MESSAGE(start_period=None, end_period=0, data="", channel_ids=[123456789, 123456789], clear_previous=False, start_now=True),
        ]
    )
]
                                     
############################################################################################

if __name__ == "__main__":
    framework.run(user_callback=None)
    