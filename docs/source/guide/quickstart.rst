
======================
Quickstart
======================
This page contains information to quickly getting started.

The first thing you need is the library installed, see :ref:`Installation`.



----------------------
Framework control
----------------------
Only one function is needed to be called for the framework to start.

The framework can be started using :func:`daf.core.run` function (and stopped with the :func:`daf.core.shutdown` function).

.. note::
    DAF is built for asynchronous usage and is using the ``asyncio`` module to run tasks.
    :func:`~daf.core.run` starts an ``asyncio`` event loop and then creates the initialization task that
    starts all the components.

    If you wish to start the framework in a program that already has a running asyncio event loop, you can use the
    :func:`daf.core.initialize` coroutine.

    .. code-block:: python

        import daf
        import asyncio

        async def some_program():
            await daf.core.initialize(...) # Starts the framework in an asyncio loop that is already running.

        asyncio.run(some_program())


Function :func:`~daf.core.run` accepts many parameters but there is only one that is most important:

:``accounts``:

    Accounts parameter is a list of :class:`daf.client.ACCOUNT` objects which represent different Discord accounts
    you can simultaneously use to shill your content.

    The below example shows a minimum definition of the accounts list. 
    For information about parameters with specific object, please use the search bar or 
    refer to the :ref:`Programming Reference`.

    .. code-block:: python
        :caption: Example

        import daf

        accounts = [
            daf.client.ACCOUNT( # Account 1
                token="DJHADJHSKJDHAKHDSKJADHKASJ", # Account token
                is_user=False,  # Is the token from an user account?
                servers=[   # List of guilds/users
                    daf.guild.GUILD(
                        snowflake=123456789, # Snowflake id of discord
                        messages=[
                            daf.message.TextMESSAGE(...),
                            daf.message.TextMESSAGE(...),
                            daf.message.VoiceMESSAGE(...)
                        ],
                        logging=True, # Log sent messages
                        remove_after=None # To automatically stop shilling
                    )
                ]
            ),

            daf.client.ACCOUNT( # Account 2
                token="JKDJSKDJALKNDSAKNDASKNDKAJS", # Account token
                is_user=False,  # Is the token from an user account?
                servers=[   # List of guilds/users
                    daf.guild.GUILD(
                        snowflake=123456789, # Snowflake id of discord
                        messages=[
                            daf.message.TextMESSAGE(...),
                            daf.message.TextMESSAGE(...),
                            daf.message.VoiceMESSAGE(...)
                        ],
                        logging=True, # Log sent messages
                        remove_after=None # To automatically stop shilling
                    )
                ]
            )
        ]


        daf.run(accounts=accounts)


.. note::
    The above example shows a bare minimum definition of the accounts list that has a 
    **manually defined** server list.

    There is also a way to automatically define the server list (and channels) based on the guild name (:ref:`Shilling scheme generation`).


After you've successfully defined your accounts list and started the framework with :func:`~daf.core.run`, the framework will run on it's own and there is nothing you need to do
from this point forward if basic periodic shilling with text messages is all you desire.


