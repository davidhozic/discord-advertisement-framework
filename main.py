import  framework


############################################################################################
#                               GUILD MESSAGES DEFINITION                                  #
############################################################################################

# MESSAGE parameters: start_period , end_period , data, channel_ids , clear_previous , start_now)

# EXAMPLE:

framework.GUILD.server_list = [
    framework.GUILD(
        863071397207212052,       # ID of server (guild)
        [                # List MESSAGE objects 
            framework.MESSAGE(start_period=None, end_period=60, data="First message", channel_ids=[863071397207212056, 909499439377416243], clear_previous=False, start_now=True),
            framework.MESSAGE(start_period=None, end_period=60, data="Second message", channel_ids=[863071397207212056, 909499439377416243], clear_previous=False, start_now=True)
        ]
    )
]
                                     
############################################################################################

if __name__ == "__main__":
    framework.run(user_callback=None)
    