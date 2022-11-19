=======================
Automatic generation
=======================
This documents describes mechanisms that can be used to automatically generate objects.

---------------------------
Shilling scheme generation
---------------------------
While the framework supports to manually define a schema, which can be time consuming if you have a lot of 
guilds to shill into and harder to manage, the framework also supports automatic generation of the schema.

You can automatically generate the schema 2 different ways:

#. Using the build-in :class:`daf.guild.AutoGUILD` and :class:`daf.message.AutoCHANNEL`,
#. Using `PyCord <https://docs.pycord.dev/en/stable/>`_ (API  wrapper) client,


AutoGUILD, AutoCHANNEL method
================================

.. _regex: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Regular_Expressions

Using this method allows you to have a completely automatically managed system of finding guilds and channels that match 
a specific regex_ pattern. It automatically finds new guilds/channels at initialization and also during normal framework operation.
This is great because it means you don't have to do much but it gives very little control of into what to shill.


Automatic GUILD generation
---------------------------
.. |AUTOGUILD| replace:: :class:`~daf.guild.AutoGUILD`
.. |GUILD| replace:: :class:`~daf.guild.GUILD`
.. |AUTOCHANNEL| replace:: :class:`~daf.message.AutoCHANNEL`

For a auto-managed GUILD list, use |AUTOGUILD| which internally generates |GUILD| instances.
Simply create a list of |AUTOGUILD| objects and then pass it to the framework.
It can be passed to the framework exactly the same way as |GUILD| (see :ref:`quickstart` (``server_list``) and :ref:`Dynamically adding objects`).

.. WARNING::

    Messages that are added to |AUTOGUILD| should have |AUTOCHANNEL| for the ``channels`` parameters,
    otherwise you will be spammed with warnings and only one guild will be shilled.

.. seealso::
    :download:`Download example <../../../Examples/Automatic Generation/autoguild.py>`.


Automatic channel generation
-----------------------------------
For a auto-managed channel list use |AUTOCHANNEL| instances.
It can be passed to xMESSAGE objects into the ``channels`` parameters instead of a list.



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
