import  framework


############################################################################################
#                               EMBED VARIABLE DEFINITON                                   #
############################################################################################
# NOTE! There can only be one embed per message but you can add more fields inside that embed!
test_embed = framework.EMBED(
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


############################################################################################
#                               GUILD MESSAGES DEFINITION                                  #
############################################################################################
framework.GUILD.server_list = [
    framework.GUILD(
        
        guild_id=123456789,         ## ID of server (guild)
        messages_to_send=[          ## List MESSAGE objects 
            framework.MESSAGE(start_period=None, end_period=15, data=(test_embed), channel_ids=[123456789], clear_previous=True, start_now=True),  
        ],
        generate_log=True 
    )
]
                                     
############################################################################################

if __name__ == "__main__":
    framework.run(  token="your_token_here",        # MANDATORY
                    is_user=False,                  # OPTIONAL
                    user_callback=None,             # OPTIONAL
                    server_log_output="Logging")    # OPTIONAL