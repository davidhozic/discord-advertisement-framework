from datetime import timedelta
import daf
from daf import discord



############################################################################################
#                               GUILD MESSAGES DEFINITION                                  #
############################################################################################

# File object representing file that will be sent
l_file1 = daf.FILE("./Examples/main_send_file.py")
l_file2 = daf.FILE("./Examples/main_send_multiple.py")

## Embedded
l_embed = daf.discord.Embed(
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
    ]
)

accounts = [
    daf.ACCOUNT( # ACCOUNT 1
        "JJJKHSAJDHKJHDKJ",
        False,
        [
            daf.USER(123456789,
                     [        
                        daf.DirectMESSAGE(None, timedelta(seconds=15), ["Test", l_file1, l_file2, l_embed]),  
                     ],
                     True)
        ]
    ),
    daf.ACCOUNT( # ACCOUNT 2
        token="JJJKHSAJDHKJHDKJ",
        is_user=False,
        servers=[
            daf.USER(
                snowflake=123456789, # ID of server (guild) or a discord.Guild object
                messages=[         # List MESSAGE objects 
                    daf.DirectMESSAGE(
                                    start_period=None,                    # If None, messages will be send on a fixed period (end period)
                                    end_period=timedelta(seconds=15),       # If start_period is None, it dictates the fixed sending period,
                                                                            # If start period is defined, it dictates the maximum limit of randomized period
                                    data=["Test", l_file1, l_file2, l_embed], # Data you want to sent to the function (Can be of types : str, embed, file, list of types to the left
                                    mode="send",                          # "send" will send a new message every time, "edit" will edit the previous message, "clear-send" will delete
                                                                            # the previous message and then send a new one
                                    start_in=timedelta(seconds=0),        # Start sending now (True) or wait until period
                                    remove_after=None                     # Remove the message never or after n-times, after specific date or after timedelta
                                    ),  
                ],
                logging=True,       # Generate file log of sent messages (and failed attempts) for this user
                remove_after=None   # When to remove the guild and it's message from the shilling list
            )
        ]
    )
]

############################################################################################

daf.run(accounts=accounts)