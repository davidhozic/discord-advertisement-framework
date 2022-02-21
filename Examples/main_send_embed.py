import  framework as fw, secret
############################################################################################
#                               EMBED VARIABLE DEFINITON                                   #
############################################################################################
# NOTE! There can only be one embed per message but you can add more fields inside that embed!


# framework.EMBED example
test_embed1 = fw.EMBED(
author_name="Developer",
author_icon="https://solarsystem.nasa.gov/system/basic_html_elements/11561_Sun.png",
fields=\
    [
        fw.EMBED_FIELD("Test 1", "Hello World", True),
        fw.EMBED_FIELD("Test 2", "Hello World 2", True),
        fw.EMBED_FIELD("Test 3", "Hello World 3", True),
        fw.EMBED_FIELD("No Inline", "This is without inline", False),
        fw.EMBED_FIELD("Test 4", "Hello World 4", True),
        fw.EMBED_FIELD("Test 5", "Hello World 5", True)
    ],
    ## ... for other arguments, see https://github.com/davidhozic/discord-advertisement-framework
)


# pycord (discord.py) Embed
test_embed2 = fw.discord.Embed( 
                                color= fw.discord.Color.dark_orange(),
                                title="Test Embed Title",
                                description="This is a discord embed",
                                # ... other, refer to Pycord documentation
                              )

# framework.EMBED from discord.Embed
test_embed_fw_2 = fw.EMBED.from_discord_embed(test_embed2) ## Converts discord.Embed into framework.EMBED



############################################################################################
#                               GUILD MESSAGES DEFINITION                                  #
############################################################################################
guilds = [
    fw.GUILD(
        guild_id=123456789,                                 # ID of server (guild)
        messages_to_send=[                                  # List MESSAGE objects
            fw.MESSAGE(
                              start_period=None,            # If None, messages will be send on a fixed period (end period)
                              end_period=15,                # If start_period is None, it dictates the fixed sending period,
                                                            # If start period is defined, it dictates the maximum limit of randomized period
                              data=test_embed1,              # Data you want to sent to the function (Can be of types : str, embed, file, list of types to the left
                                                            # or function that returns any of above types(or returns None if you don't have any data to send yet), 
                                                            # where if you pass a function you need to use the fw.FUNCTION decorator on top of it ).
                              channel_ids=[123456789],      # List of ids of all the channels you want this message to be sent into
                              mode="send",          # Clear all discord messages that originated from this MESSAGE object
                              start_now=True                # Start sending now (True) or wait until period
                              ),

            fw.MESSAGE(
                              start_period=None,
                              end_period=15,

                              data=test_embed_fw_2, 

                              channel_ids=[123456789],
                              mode="send",
                              start_now=True
                              ),
        ],
        generate_log=True           ## Generate file log of sent messages (and failed attempts) for this server 
    )
]
                                     
############################################################################################

if __name__ == "__main__":
    fw.run(  token=secret.C_TOKEN,           # MANDATORY,
                    server_list=guilds,             # MANDATORY
                    is_user=False,                  # OPTIONAL
                    user_callback=None,             # OPTIONAL
                    server_log_output="History",    # OPTIONAL
                    debug=True)                     # OPTIONAL