import  framework, discord




############################################################################################
#                               GUILD MESSAGES DEFINITION                                  #
############################################################################################

## Discord embed
l_embed = discord.Embed()
l_embed.add_field(name="First_Field", value="This is embed field 1")
l_embed.add_field(name="Second_Field", value="This is embed field 2")

framework.GUILD.server_list = [
    framework.GUILD(
        guild_id=1234,               # ID of server (guild)
        messages_to_send=[                   # List MESSAGE objects 
            framework.MESSAGE(start_period=None, end_period=60, data=l_embed, channel_ids=[1234, 1234], clear_previous=False, start_now=True),  ## Will sent a message every 60 seconds
        ],
        generate_log=True 
    )
]
                                     
############################################################################################

if __name__ == "__main__":
    framework.run(user_callback=None)
    