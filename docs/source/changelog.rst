Changelog
========================
.. seealso:: 
    `Releases <https://github.com/davidhozic/discord-advertisement-framework/releases>`_

.. note:: 
    The library first started as a single file script that I didn't make versions of.
    When I decided to turn it into a library, I've set the version number based on the amount of commits I have made since the start.

v2.1
----------------------
- ``timedelta`` object on ``start_period/end_period`` parameters
- Replaced ``start_now`` with ``start_in`` parameter, deprecated use of bool value
- :class:`framework.TextMESSAGE` and :class:`framework.VoiceMESSAGE` now check if the given channels are actually inside the guild
- Fixed message slippage in case of slow Discord API calls or rate limit

.. figure:: images/changelog_2_1_slippage_fix.png
    
    Fixed message slippage in case of slow Discord API calls or rate limit
  

v2.0
----------------------
- New cool looking web documentation (the one you're reading now)
- Added volume parameter to :class:`framework.VoiceMESSAGE`
- Changed ``channel_ids`` to ``channels`` for :class:`framework.VoiceMESSAGE` and :class:`framework.TextMESSAGE`. It can now also accept discord.<Type>Channel objects.
- Changed ``user_id``/ ``guild_id`` to ``snowflake`` in :class:`framework.GUILD` and :class:`framework.USER`. This parameter now also accept discord.Guild (:class:`framework.GUILD`) and discord.User (:class:`framework.USER`)
- Added ``.update`` method to some objects for allowing dynamic modifications of initialization parameters.
- :class:`framework.AUDIO` now also accepts a YouTube link for streaming YouTube videos.
- New :ref:`Exceptions` system - most functions now raise exceptions instead of just returning bool to allow better detection of errors.
- Bug fixes and other small improvements.

v1.9.0
----------------------
- Added support for logging into a SQL database (MS SQL Server only). See :ref:`relational database log`.
- :func:`framework.run` function now accepts discord.Intents.
- :func:`framework.add_object` and :func:`framework.remove_object` functions created to allow for dynamic modification of the shilling list.
- Other small improvements.

v1.8.1
----------------------
- JSON file logging.
- Automatic channel removal if channel get's deleted and message removal if all channels are removed.
- Improved debug messages.

v1.7.9
----------------------
- :class:`framework.DirectMESSAGE` and :class:`framework.USER` classes created for direct messaging.


