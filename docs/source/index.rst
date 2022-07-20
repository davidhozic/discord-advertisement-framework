=========================================================
Index
=========================================================
The Discord advertisement framework is a tool that allows easy advertising on Discord.

.. toctree::
    :hidden:

    ref
    

Reference
---------------
- `Github <https://github.com/davidhozic/discord-advertisement-framework>`_
- `Releases <https://github.com/davidhozic/discord-advertisement-framework/releases>`_
- :ref:`Programming Reference`

Key features
-------------------
- Periodic advertisement to **Direct (Private) Messages**, **Text channels** and **Voice channels**
- Advertising with either static data (text, embed, files, audio) or **dynamic data** (the data is obtained thru a function dynamically)
- Logging of send attempts with **JSON** file logs or to a **SQL** server (Microsoft SQL Server only).
- Ability to add additional application layers with help of asyncio
- Easy to setup
- Ability to run on **user** accounts or **bot** accounts

.. warning::
    While running this on user accounts is possible, it is not recommended since it is against Discord's ToS.


Installation
-------------------

To install the framework use one of the following:

.. code-block:: bash

    # Windows
    python -m pip install discord-advert-framework

.. code-block:: bash

    # Windows
    py -3 -m pip install discord-advert-framework

.. code-block:: bash
    
    # Linux
    python3 -m pip install discord-advert-framework


Example
-----------
.. code-block:: python

    """
    ~ Example file ~
    This file shows how you can make a script that automatically generates the server
    list based on the `allowed_strings` list (contains strings that must appear in the channel name we want to shill into).

    We pass the framework a user_callback function named `find_advertisement_channels` which autofills the servers list with GUILD objects.
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
        # Returns the client to send commands to discord, for more info about client see https://docs.pycord.dev/en/master/api.html?highlight=discord%20client#discord.Client
        client = fw.get_client()  
        
        for guild in client.guilds:  # Iterate thru all the guilds where the bot is in
            channels = []
            for channel in guild.text_channels: # Iterate thru all the text channels in the guild
                if any([x in channel.name for x in allowed_strings]): # Check if any of the strings in allowed_strings are in the channel name
                    channels.append(channel.id) # If so, add the channel id to the list
            
            # Add the guild to the internal shilling list
            await fw.core.add_object(   
                fw.GUILD(
                    guild.id,                               # Guild id
                    [                                       # List of messages
                        fw.TextMESSAGE(None,                    # Start period
                                    5,                       # End period
                                    data_to_shill,           # Data that will be sent
                                    channels,                # List of channels to send the message to            
                                    "send",                  # Sending moode (send, edit, clear-send)
                                    True                     # Should the message be sent immediately after adding it to the list
                        )                                   
                    ],
                    True                                    # Should the framework generate a log of sent messages for this guild
                )
            )


    fw.run(
        token="OSDSJ44JNnnJNJ2NJDBWQUGHSHFAJSHDUQHFDBADVAHJVERAHGDVAHJSVDE",   # Example token
        server_list=servers,
        user_callback=find_advertisement_channels
    )
