import daf, secret
from daf import discord
from datetime import timedelta
############################################################################################
#                               EMBED VARIABLE DEFINITON                                   #
############################################################################################
# NOTE! There can only be one embed per message but you can add more fields inside that embed!


# daf.EMBED example
test_embed1 = daf.EMBED(
author_name="Developer",
author_icon="https://solarsystem.nasa.gov/system/basic_html_elements/11561_Sun.png",
fields=\
    [
        discord.EmbedField("Test 1", "Hello World", True),
        discord.EmbedField("Test 2", "Hello World 2", True),
        discord.EmbedField("Test 3", "Hello World 3", True),
        discord.EmbedField("No Inline", "This is without inline", False),
        discord.EmbedField("Test 4", "Hello World 4", True),
        discord.EmbedField("Test 5", "Hello World 5", True)
    ],
    ## ... for other arguments, see https://github.com/davidhozic/discord-advertisement-framework
)


# pycord (discord.py) Embed
test_embed2 = daf.discord.Embed( 
                                color= daf.discord.Color.dark_orange(),
                                title="Test Embed Title",
                                description="This is a discord embed",
                                # ... other, refer to Pycord documentation
                              )

# daf.EMBED from discord.Embed
test_embed_fw_2 = daf.EMBED.from_discord_embed(test_embed2) ## Converts discord.Embed into daf.EMBED



############################################################################################
#                               GUILD MESSAGES DEFINITION                                  #
############################################################################################
guilds = [
    daf.GUILD(
        snowflake=123456789,                                 # ID of server (guild) or a discord.Guild object
        messages=[                                  # List MESSAGE objects
            daf.TextMESSAGE(
                              start_period=None,            # If None, messages will be send on a fixed period (end period)
                              end_period=timedelta(seconds=15),                # If start_period is None, it dictates the fixed sending period,
                                                            # If start period is defined, it dictates the maximum limit of randomized period
                              data=test_embed1,              # Data you want to sent to the function (Can be of types : str, embed, file, list of types to the left
                                                            # or function that returns any of above types(or returns None if you don't have any data to send yet), 
                                                            # where if you pass a function you need to use the daf.FUNCTION decorator on top of it ).
                              channels=[123456789],      # List of ids of all the channels you want this message to be sent into
                              mode="send",                  # "send" will send a new message every time, "edit" will edit the previous message, "clear-send" will delete
                                                            # the previous message and then send a new one
                              start_in=timedelta(seconds=0)                # Start sending now (True) or wait until period
                              ),

            daf.TextMESSAGE(
                              start_period=None,
                              end_period=timedelta(seconds=15),

                              data=test_embed_fw_2, 

                              channels=[123456789],
                              mode="send",
                              start_in=timedelta(seconds=0)
                              ),
        ],
        logging=True           ## Generate file log of sent messages (and failed attempts) for this server 
    )
]
                                     
############################################################################################
daf.run(token=secret.C_TOKEN,        
        server_list=guilds,
        is_user=False)