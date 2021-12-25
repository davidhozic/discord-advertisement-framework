import  framework, discord




############################################################################################
#                               GUILD MESSAGES DEFINITION                                  #
############################################################################################

# File object representing file that will be sent
l_file1 = framework.FILE("./Examples/main_send_file.py")
l_file2 = framework.FILE("./Examples/main_send_multiple.py")

## Discord embed
l_embed = discord.Embed()
l_embed.add_field(name="First_Field", value="This is embed field 1")
l_embed.add_field(name="Second_Field", value="This is embed field 2")



framework.GUILD.server_list = [
    framework.GUILD(
        guild_id=1234,            # ID of server (guild)
        messages_to_send=[        # List MESSAGE objects 
            # Will send "Hello world", 2 files and an embed to channels every 60 seconds
            framework.MESSAGE(start_period=None, end_period=60, data=["Hello world", l_file2, l_file1, l_embed], channel_ids=[1234, 1234], clear_previous=False, start_now=True)
        ],
        generate_log=True 
    )
]
                                     
############################################################################################

if __name__ == "__main__":
    framework.run(user_callback=None)
    