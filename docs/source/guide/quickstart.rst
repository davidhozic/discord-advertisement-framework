
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


Function :func:`~daf.core.run` accepts many parameters but there are **3 which are most important**:

- ``token``
    This is the Discord account access token, it can be obtained the following way:

    .. tab-set::
        
        .. tab-item:: Bot accounts

            1. Visit the `Developer Portal <https://discord.com/developers/>`_
            2. Select your application
            3. Click on the "Bot" tab
            4. Click "Copy token" - if only "reset" exists, click on "reset" and then "Copy token"

        .. tab-item:: User accounts
        
            Follow `instructions <https://www.youtube.com/results?search_query=discord+get+user+token>`_

    .. code-block:: python
        :emphasize-lines: 5

        import daf


        daf.run(
            token="JDJSDJAHDSAHBDJABEJHQGEGSAGEJHSGJGEJSHG", # Some account token
        )
        
- ``is_user``
    Set this to True if the ``token`` parameter is from an user account or False if it is from a bot account.

    .. code-block:: python
        :emphasize-lines: 6

        import daf


        daf.run(
            token="JDJSDJAHDSAHBDJABEJHQGEGSAGEJHSGJGEJSHG", # Some account token
            is_user=True # Set this to True, if the above token is from an user account.
        )

- ``server_list``
    This parameter accepts a list of :class:`~daf.guild.GUILD` / :class:`~daf.guild.USER` objects and represents the servers to which the framework will shill.
    The below block shows a sample definition of the server list, which will send text messages. For full parameters see :class:`~daf.guild.GUILD` / :class:`~daf.guild.USER`
    and :class:`daf.message.TextMESSAGE` for the TextMESSAGE parameters.

    .. note::
        Snowflake ID is a unique ID representing resources like guilds and channels. 
        It can be obtained by enabling developer mode, then right clicking on the resource (eg. guild) and last
        left clicking ``Copy ID``.
        
        `Obtaining snowflake <https://support.discord.com/hc/en-us/articles/206346498-Where-can-I-find-my-User-Server-Message-ID->`_.

    .. only:: html
        
        .. literalinclude:: ../../../Examples/Message Types/TextMESSAGE/main_send_string.py
            :emphasize-lines: 4, 5, 8, 21, 32



After you've successfully defined your server list and started the framework with :func:`~daf.core.run`, the framework will run on it's own and there is nothing you need to do
from this point forward if basic periodic shilling with text messages is all you desire.