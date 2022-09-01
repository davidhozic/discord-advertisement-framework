
Getting started
======================
This page contains a guide to getting started with the shiller.



Minimal example
----------------------
This is a minimal example of how to use the shiller. 

.. note:: 
    The example shows you how to shill "Hello World" every 5 seconds to a manually defined list of servers, however this is not what framework
    is limited to (see `Examples <https://github.com/davidhozic/discord-advertisement-framework/tree/master/Examples>`_).
    
.. seealso:: 
    :download:`Download more examples <../../Examples/Examples.zip>`
    
    `Examples on GitHub <https://github.com/davidhozic/discord-advertisement-framework/tree/master/Examples>`_



To start shilling you need to:

1. Import the library with ``import daf``
2. Define a server list
3. Start the shilling with :ref:`run` function. 


For help with the :ref:`GUILD`, :ref:`TextMESSAGE` object and see :ref:`Programming Reference`.


.. code-block:: python

    from datetime import timedelta
    

    # Define a server list
    servers = [
        daf.GUILD(
            snowflake=123456789012345678, # The snowflake id of the guild (This can be obtained by enabling developer mode and then right clicking on the guild's icon)
            messages=[
                daf.TextMESSAGE(None, timedelta(seconds=5), "Hello world!", [123456789012345678], "send", True) # start_period, end_period, data, channels, mode, start_now
            ],
            logging=True # Generate logs for each sent message
        )
    ]

    daf.run(
        token="DNASNDANDASKJNDAKSJDNASKJDNASKJNSDSAKDNAKLSNDSKAJDN", # The authorization token
        servers=servers # The server list
    )

.. seealso:: 
    :ref:`snowflake id`
    
    :ref:`authorization token`    


Snowflake ID
----------------------
To get the snowflake id you need to first enable `Developer Mode <https://support.discord.com/hc/en-us/articles/206346498-Where-can-I-find-my-User-Server-Message-ID->`_.
Then just right click on any guild or server and click ``Copy ID`` to get the snowflake ID.


Authorization token
---------------------
The authorization token is a token that is needed to communicate thru the Discord API.

Bot accounts
~~~~~~~~~~~~~~~~~~~~~~
1. Visit the `Developer Portal <https://discord.com/developers/>`_
2. Select your application
3. Click on the "Bot" tab
4. Click "Copy token" - if only "reset" exists, click on "reset" and then "Copy token"

User accounts
~~~~~~~~~~~~~~~~~~~~~~~
Follow `instructions <https://www.youtube.com/results?search_query=discord+get+user+token>`_


