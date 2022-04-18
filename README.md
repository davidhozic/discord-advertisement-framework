#  **DISCORD ADVERTISEMENT FRAMEWORK (BOT) - DAF**
![PyPI](https://img.shields.io/pypi/v/discord-advert-framework?color=green&style=for-the-badge)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/discord-advert-framework?style=for-the-badge)](https://pypi.org/project/Discord-Advert-Framework/)
[![CodeFactor Grade](https://img.shields.io/codefactor/grade/github/davidhozic/discord-advertisement-framework?style=for-the-badge)](https://www.codefactor.io/repository/github/davidhozic/discord-advertisement-framework)

The Discord advertisement framework is a tool that allows easy advertising on Discord.

# **Key features**
- Periodic advertisement to **DMs**, **Text channels** and **Voice channels**
- Advertising with either static data or **dynamic data** (function call)
- JSON logs of sent messages
- Ability to add additional application layers with help of asyncio


# **FULL documentation**
The **full documentation** can be found in **[DOC.md](https://github.com/davidhozic/discord-advertisement-framework/blob/master/DOC.md)**


# **Installation**
To install the framework use one of the following:
```py
# Windows
python -m pip install discord-advert-framework
```
```py
# Windows
py -3 -m pip install discord-advert-framework
```
```py
# Linux
python3 -m pip install discord-advert-framework
```

# **Example**
```py
import  framework, secret
from framework import discord



############################################################################################
#                               GUILD MESSAGES DEFINITION                                  #
############################################################################################

# File object representing file that will be sent
l_file1 = framework.FILE("./Examples/main_send_file.py")
l_file2 = framework.FILE("./Examples/main_send_multiple.py")

## Embedded
l_embed = framework.EMBED(
author_name="Developer",
author_icon="https://solarsystem.nasa.gov/system/basic_html_elements/11561_Sun.png",
fields=\
    [
        framework.EmbedFIELD("Test 1", "Hello World", True),
        framework.EmbedFIELD("Test 2", "Hello World 2", True),
        framework.EmbedFIELD("Test 3", "Hello World 3", True),
        framework.EmbedFIELD("No Inline", "This is without inline", False),
        framework.EmbedFIELD("Test 4", "Hello World 4", True),
        framework.EmbedFIELD("Test 5", "Hello World 5", True)
    ]
)


guilds = [
    framework.GUILD(
        guild_id=123456789,                                 # ID of server (guild)
        messages_to_send=[                                  # List MESSAGE objects
            framework.TextMESSAGE(
                              start_period=None,            # If None, messages will be send on a fixed period (end period)
                              end_period=15,                # If start_period is None, it dictates the fixed sending period,
                                                            # If start period is defined, it dictates the maximum limit of randomized period
                              data=["Hello World",          # Data you want to sent to the function (Can be of types : str, embed, file, list of types to the left
                                    l_file1,                # or function that returns any of above types(or returns None if you don't have any data to send yet),
                                    l_file2,                # where if you pass a function you need to use the framework.FUNCTION decorator on top of it ).
                                    l_embed],           
                              channel_ids=[123456789],      # List of ids of all the channels you want this message to be sent into
                              mode="send",                  # "send" will send a new message every time, "edit" will edit the previous message, "clear-send" will delete
                                                            # the previous message and then send a new one
                              start_now=True                # Start sending now (True) or wait until period
                              ),  
        ],
        generate_log=True           ## Generate file log of sent messages (and failed attempts) for this server 
    )
]

                                     
############################################################################################

if __name__ == "__main__":
    framework.run(  token="BOT TOKEN",              # MANDATORY,
                    server_list=guilds,             # MANDATORY
                    is_user=False,                  # OPTIONAL
                    user_callback=None,             # OPTIONAL
                    server_log_output="History",    # OPTIONAL
                    debug=True)                     # OPTIONAL
```
