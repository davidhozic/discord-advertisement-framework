import  discron, secret
from discron import discord



############################################################################################
#                               GUILD MESSAGES DEFINITION                                  #
############################################################################################

# File object representing file that will be sent
l_file1 = discron.FILE("./Examples/main_send_file.py")
l_file2 = discron.FILE("./Examples/main_send_multiple.py")

## Embedded
l_embed = discron.EMBED(
author_name="Developer",
author_icon="https://solarsystem.nasa.gov/system/basic_html_elements/11561_Sun.png",
fields=\
    [
        discron.EmbedFIELD("Test 1", "Hello World", True),
        discron.EmbedFIELD("Test 2", "Hello World 2", True),
        discron.EmbedFIELD("Test 3", "Hello World 3", True),
        discron.EmbedFIELD("No Inline", "This is without inline", False),
        discron.EmbedFIELD("Test 4", "Hello World 4", True),
        discron.EmbedFIELD("Test 5", "Hello World 5", True)
    ]
)

guilds = [
    discron.USER(
        user_id=123456789,                                 # ID of server (guild)
        messages_to_send=[                                  # List MESSAGE objects
            discron.DirectMESSAGE(
                              start_period=None,            # If None, messages will be send on a fixed period (end period)
                              end_period=15,                # If start_period is None, it dictates the fixed sending period,
                                                            # If start period is defined, it dictates the maximum limit of randomized period
                              data=["Hello World",          # Data you want to sent to the function (Can be of types : str, embed, file, list of types to the left
                                    l_file1,                # or function that returns any of above types(or returns None if you don't have any data to send yet),
                                    l_file2,                # where if you pass a function you need to use the framework.FUNCTION decorator on top of it ).
                                    l_embed],           
                              mode="send",                  # "send" will send a new message every time, "edit" will edit the previous message, "clear-send" will delete
                                                            # the previous message and then send a new one
                              start_now=True                # Start sending now (True) or wait until period
                              ),  
        ],
        generate_log=True                                   ## Generate file log of sent messages (and failed attempts) for this user
    )
]

                                     
############################################################################################

if __name__ == "__main__":
    discron.run(  token=secret.C_TOKEN,               # MANDATORY
                    intents=discord.Intents.default(),  # OPTIONAL (see https://docs.pycord.dev/en/master/intents.html)
                    server_list=guilds,                 # MANDATORY
                    is_user=False,                      # OPTIONAL
                    user_callback=None,                 # OPTIONAL
                    server_log_output="History",        # OPTIONAL
                    debug=True)                         # OPTIONAL