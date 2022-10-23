=======================
Automatic generation
=======================

This documents describes mechanisms that can be used to automatically generate objects.
All automatic generation is done in the :mod:`daf.gen` module.

This module allows to automatically generate the shilling scheme (:class:`~daf.guild.GUILD` / :ref:`Messages` objects) as well as advertisement content based on a 
machine learning model that the user themselves train.

---------------------------
Shilling scheme generation
---------------------------
While the framework supports to manually define a schema, which can be time consuming if you have a lot of 
guilds to shill into and harder to manage, the framework also supports automatic generation of the schema.

You can automatically generate the schema 2 different ways:

1. Using `PyCord <https://docs.pycord.dev/en/stable/>`_ (API  wrapper) client,
2. Using the build-in :class:`daf.gen.AutoGUILD` and :class:`daf.gen.AutoCHANNEL`, (requires **DAF v2.3+**)

PyCord scheme generation method
================================
This is done by using the :class:`discord.Client` object.

:class:`discord.Client` object should not be created manually as the framework automatically creates it.
To obtain the client, call :func:`daf.client.get_client` function.
To find guilds, we will be using the :py:attr:`discord.Client.guilds` property which will return a list of :py:attr:`discord.Guild` objects
and then on each guild inside the list, we will be using the :py:attr:`discord.Guild.text_channels` property which will return a list of
:class:`discord.TextChannel` objects.

Then we will use the :func:`daf.core.add_object` function to add objects to the shilling list (:ref:`Dynamically adding objects`)


.. code-block:: python
    :caption: Automatic generation using PyCord thru the user_callback coroutine

    from datetime import timedelta
    import daf
    
    async def main():
        # Get discord.Client object
        client = daf.get_client()
        
        # Iterate thru all guilds
        for guild in client.guilds:
            # Iterate thru all channels
            channels = []
            for channel in guild.text_channels:
                # Channel names must contain word "shill"
                if "shill" in channel.name:
                    channels.append(channel)
            
            # at least one channel was found
            if len(channels):
                await daf.core.add_object(
                    daf.guild.GUILD(snowflake=guild, messages=[
                            daf.message.TextMESSAGE(None,
                                                    timedelta(seconds=60), 
                                                    data="Hello World",
                                                    channels=channels)
                        ]
                    )
                )


    daf.run(token="KDHJSKLJHDKAJDHS", is_user=False, user_callback=main)


AutoGUILD, AutoCHANNEL method
================================

.. warning::
    This will be added in **v2.3**