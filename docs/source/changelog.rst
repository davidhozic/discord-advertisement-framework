========================
Changelog
========================
.. |BREAK_CH| replace:: **[Breaking change]**

.. |POTENT_BREAK_CH| replace:: **[Potentially breaking change]**

------------------------
Info
------------------------

.. seealso:: 
    `Releases <https://github.com/davidhozic/discord-advertisement-framework/releases>`_  

.. note:: 
    The library first started as a single file script that I didn't make versions of.
    When I decided to turn it into a library, I've set the version number based on the amount of commits I have made since the start.


Glossary
======================
.. glossary::

    |BREAK_CH|
        Means that the change will break functionality from previous version.

    |POTENT_BREAK_CH|
        The change could break functionality from previous versions but only if it
        was used in a certain way.

----------------------
Releases
----------------------

v2.5.2
=============
- Fixed ``typechecked`` module error


v2.5.1
==========
- Fixed failure without SQL

v2.5
==========
- |BREAK_CH| Removed ``EMBED`` object, use ``daf.discord.Embed`` instead.
- |BREAK_CH| Removed ``timing`` module since it only contained deprecated objects.
- |BREAK_CH| Minumum Python version has been bumbed to **Python v3.10**.
- WEB INTEGRATION:
  
  - Automatic login and (semi-automatic) guild join though :class:`daf.web.SeleniumCLIENT`.
  - Automatic server discovery though :class:`daf.web.GuildDISCOVERY`


v2.4.3
=========
- Fixed missing documentation members


v2.4.2 (v2.3.4)
=================
- Fixed channel verification bug:

  - Fixes bug where messages try to be sent into channels that have not passed verification (complete button)

v2.4
=============
- Multiple accounts support:
  
  - Added :class:`daf.client.ACCOUNT` for running multiple accounts at once. Proxies are strongly recommended!
  - Deprecated use of:
    
    - token,
    - is_user,
    - proxy,
    - server_list,
    - intents
    
    inside the :func:`daf.core.run` function.

  - New function :func:`daf.core.get_accounts` that returns the list of all running accounts in the framework.

- Deprecated :func:`~daf.core.add_object` and :func:`~daf.core.remove_object` functions accepting API wrapper objects or ``int`` type for the ``snowflake`` parameter.
- Deprecated ``daf.core.get_guild_user`` function due to multiple accounts support.
- Deprecated ``daf.client.get_client`` function due to multiple accounts support.

v2.3
=============
- |BREAK_CH| Removed ``exceptions`` module, meaning that there are no DAFError derived exceptions from this version on.
  They are replaced with build-in Python exceptions.
- Automatic scheme generation and management:

  - :class:`daf.guild.AutoGUILD` class for auto-managed GUILD objects.
  - :class:`daf.message.AutoCHANNEL` class for auto-managed channels inside message.

- Debug levels:

  - Added deprecated to :class:`~daf.logging.tracing.TraceLEVELS`.
  - Changed the :func:`daf.core.run`'s debug parameter to accept a value from :class:`~daf.logging.tracing.TraceLEVELS`, to dictate
    what level trace should be displayed.

- :ref:`Messages` objects period automatically increases if it is less than slow-mode timeout.
- The :ref:`data_function`'s input function can now also be async.

v2.2
===========
- ``user_callback`` parameter for function :func:`daf.core.run` can now also be a regular function instead of just ``async``.
- Deprecated :class:`daf.dtypes.EMBED`, use :class:`discord.Embed` instead.
- |BREAK_CH| Removed ``get_sql_manager`` function.
- :func:`daf.core.run`:
    + Added ``logging`` parameter
    + Deprecated parameters ``server_log_output`` and ``sql_manager``.
- Logging manager objects: LoggerJSON, LoggerCSV, LoggerSQL
- New :func:`daf.logging.get_logger` function for retrieving the logger object used.
- :func:`daf.core.initialize` for manual control of asyncio (same as :func:`daf.core.run` except it is async)
- SQL:
    + SQL logging now supports **Microsoft SQL Server, MySQL, PostgreSQL and SQLite databases**.
    + |BREAK_CH| :class:`~daf.logging.sql.LoggerSQL`'s parameters are re-arranged, new parameters of which, the ``dialect`` (mssql, sqlite, mysql, postgresql) parameter must be passed.
- Development:
    + ``doc_category`` decorator for automatic documentation
    + Removed ``common`` module and moved constants to appropriate modules

v2.1.4
===========
Bug fixes:

- ``Fix incorrect parameter name in documentation``.

v2.1.3
===========
Bug fixes:

- ``[Bug]: KeyError: 'code' on rate limit #198``.

v2.1.2
===========
Bug fixes:

- #195 VoiceMESSAGE did not delete deleted channels.
- Exception on initialization of static server list in case any of the messages had failed their initialization.

v2.1.1
===========
- Fixed ``[Bug]: Predefined servers' errors are not suppressed #189``.
- Support for readthedocs.


v2.1
===========
- Changed the import ``import framework`` to ``import daf``. Using ``import framework`` is now deprecated.
- ``remove_after`` parameter:
    Classes: :class:`daf.guild.GUILD`, :class:`daf.guild.USER`, :class:`daf.message.TextMESSAGE`, :class:`daf.message.VoiceMESSAGE`, :class:`daf.message.DirectMESSAGE`

    now support the remove_after parameter which will remove the object from the shilling list when conditions met.
- Proxies:
    Added support for using proxies.
    To use a proxy pass the :func:`daf.run` function with a ``proxy`` parameter
- discord.EmbedField:
    |BREAK_CH| Replaced discord.EmbedField with discord.EmbedField.
- timedelta:
    start_period and end_period now support ``timedelta`` object to specify the send period.
    Use of ``int`` is deprecated

    |POTENT_BREAK_CH| Replaced ``start_now`` with ``start_in`` parameter, deprecated use of bool value.
- Channel checking:
    :class:`daf.TextMESSAGE` and :class:`daf.VoiceMESSAGE` now check if the given channels are actually inside the guild
- Optionals:
    |POTENT_BREAK_CH| Made some functionality optional: ``voice``, ``proxy`` and ``sql`` - to install use ``pip install discord-advert-framework[dependency here]``
- CLIENT:
    |BREAK_CH| Removed the CLIENT object, discord.Client is now used as the CLIENT class is no longer needed due to improved startup
- Bug fixes:
    Time slippage correction:
        This occurred if too many messages were ready at once, which resulted in discord's rate limit,
        causing a permanent slip.

        .. figure:: images/changelog_2_1_slippage_fix.png    

            Time slippage correction

    Slow mode correction:
        Whenever a channel was in slow mode, it was not properly handled. This is now fixed.


v2.0
===========
- New cool looking web documentation (the one you're reading now)
- Added volume parameter to :class:`daf.VoiceMESSAGE`
- Changed ``channel_ids`` to ``channels`` for :class:`daf.VoiceMESSAGE` and :class:`daf.TextMESSAGE`. It can now also accept discord.<Type>Channel objects.
- Changed ``user_id``/ ``guild_id`` to ``snowflake`` in :class:`daf.GUILD` and :class:`daf.USER`. This parameter now also accept discord.Guild (:class:`daf.GUILD`) and discord.User (:class:`daf.USER`)
- Added ``.update`` method to some objects for allowing dynamic modifications of initialization parameters.
- :class:`daf.AUDIO` now also accepts a YouTube link for streaming YouTube videos.
- New :ref:`Exceptions` system - most functions now raise exceptions instead of just returning bool to allow better detection of errors.
- Bug fixes and other small improvements.

v1.9.0
===========
- Added support for logging into a SQL database (MS SQL Server only). See :ref:`relational database log (SQL)`.
- :func:`daf.run` function now accepts discord.Intents.
- :func:`daf.add_object` and :func:`daf.remove_object` functions created to allow for dynamic modification of the shilling list.
- Other small improvements.

v1.8.1
===========
- JSON file logging.
- Automatic channel removal if channel get's deleted and message removal if all channels are removed.
- Improved debug messages.

v1.7.9
===========
- :class:`daf.DirectMESSAGE` and :class:`daf.USER` classes created for direct messaging.


