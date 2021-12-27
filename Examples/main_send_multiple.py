import  framework, discord




############################################################################################
#                               GUILD MESSAGES DEFINITION                                  #
############################################################################################

# File object representing file that will be sent
l_file1 = framework.FILE("./Examples/main_send_file.py")
l_file2 = framework.FILE("./Examples/main_send_multiple.py")

## Embedded
l_embed = framework.EMBED(
author_name="Developer",
author_image_url="https://solarsystem.nasa.gov/system/basic_html_elements/11561_Sun.png",
fields=\
    [
        framework.EMBED_FIELD("Test 1", "Hello World", True),
        framework.EMBED_FIELD("Test 2", "Hello World 2", True),
        framework.EMBED_FIELD("Test 3", "Hello World 3", True),
        framework.EMBED_FIELD("No Inline", "This is without inline", False),
        framework.EMBED_FIELD("Test 4", "Hello World 4", True),
        framework.EMBED_FIELD("Test 5", "Hello World 5", True)
    ]
)


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
    