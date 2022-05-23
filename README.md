#  **DISCORD ADVERTISEMENT FRAMEWORK (BOT) - DAF**
![PyPI](https://img.shields.io/pypi/v/discord-advert-framework?color=green&style=for-the-badge)
[![CodeFactor Grade](https://img.shields.io/codefactor/grade/github/davidhozic/discord-advertisement-framework?style=for-the-badge)](https://www.codefactor.io/repository/github/davidhozic/discord-advertisement-framework)

The Discord advertisement framework is a tool that allows easy advertising on Discord.

# **FULL documentation**
For documentation on all the object in the framework and section on **GETTING STARTED** see **[DOC.md](https://github.com/davidhozic/discord-advertisement-framework/blob/master/DOC.md)**

# **Key features**
- Periodic advertisement to **Direct (Private) Messages**, **Text channels** and **Voice channels**
- Advertising with either static data or **dynamic data** (function call)
- Logging of send attempts with **JSON** file logs or to a **SQL** server (Microsoft SQL Server only).
- Ability to add additional application layers with help of asyncio
- Easy to setup


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
"""
~ Example file ~
This file shows how you can make a script that automatically generates the server
list based on the `allowed_strings` list (contains strings that must appear in the channel name we want to shill into).

We pass the framework a user_callback function named `find_advertisement_channels` which autofills the `servers` list with GUILD objects.
"""
import framework as fw


# Create a list in which we will automatically add guilds
allowed_strings = {"shill", "advert", "promo"}
data_to_shill = (     # Example data set
                "Hello World", 
                fw.EMBED(title="Example Embed",
                         color=fw.EMBED.Color.blue(),
                         description="This is a test embed")
                )


servers = []

async def find_advertisement_channels():
    # This function get's called after discord has been conencted but
    # framework not yet initialized
    client = fw.get_client()  # Returns the client to send commands to discord, for more info about client see https://docs.pycord.dev/en/master/api.html?highlight=discord%20client#discord.Client

    # Iterate thru all the guilds and channels
    # All of the objects inside the client are objects from the libarary Pycord which is an API wrapper used by this framework https://docs.pycord.dev/en/master/index.html
    for guild in client.guilds:
        channels_to_shill = []  # Channels that we will shill into for this guild

        fw.trace(f"Channels found for guild {guild.name}: {[channel.name for channel in channels_to_shill]}")
        for channel in guild.text_channels: # Only search text channels
            chname = channel.name
            if any([string in chname for string in allowed_strings]): # Make a list with bool values where we check if string from `allowed_strings` is in the channel name,
                                                                      # and then check if any of the expressions were True (there indeed is a channel with one of those strings)
                channels_to_shill.append(channel.id) # .id because the framework accepts ids

        # Append a new GUILD object with one text message that is sent to the channels that were found in the previous section        
        servers.append(
            fw.GUILD(
                guild_id=guild.id,
                messages_to_send=[
                    # Shill every minute, send `data_to_shill` into `channels_to_shill`. "send" - send new message each period, `True` - start now
                    fw.TextMESSAGE(None, 1 * fw.C_MINUTE_TO_SECOND, data_to_shill, channels_to_shill, "send", True)
                ],
                generate_log=True
            )
        )
    
    fw.trace(f"Shilling into {len(servers)} guild{'s' if len(servers) > 1 else ''}")


fw.run(
    token="OSDSJ44JNnnJNJ2NJDBWQUGHSHFAJSHDUQHFDBADVAHJVERAHGDVAHJSVDE",   # Example token
    server_list=servers,
    user_callback=find_advertisement_channels
)
```
