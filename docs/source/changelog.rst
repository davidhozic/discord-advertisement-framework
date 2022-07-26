Changelog
========================
.. seealso:: 
    `Releases <https://github.com/davidhozic/discord-advertisement-framework/releases>`_

.. note:: 
    The library first started as a single file script that I didn't make versions of.
    When I decided to turn it into a library, I've set the version number based on the amount of commits I have made since the start.

v2.0
----------------------
- New cool looking web documentation (the one you're reading now)
- Added volume parameter to :ref:`VoiceMESSAGE`
- Changed ``channel_ids`` to ``channels`` for :ref:`VoiceMESSAGE` and :ref:`TextMESSAGE`. It can now also accept discord.<Type>Channel objects.
- Changed ``user_id``/ ``guild_id`` to ``snowflake`` in :ref:`GUILD` and :ref:`USER`. This parameter now also accept discord.Guild (:ref:`GUILD`) and discord.User (:ref:`USER`)
- Added ``.update`` method to some objects for allowing dynamic modifications of initialization parameters.
- :ref:`AUDIO` now also accepts a YouTube link for streaming YouTube videos.
- New :ref:`Exceptions` system - most functions now raise exceptions instead of just returning bool to allow better detection of errors.
- Bug fixes and other small improvements.

v1.9.0
----------------------
- Added support for logging into a SQL database (MS SQL Server only). See :ref:`relational database log`.
- :ref:`run` function now accepts discord.Intents.
- :ref:`add_object` and :ref:`remove_object` functions created to allow for dynamic modification of the shilling list.
- Other small improvements.

v1.8.1
----------------------
- JSON file logging.
- Automatic channel removal if channel get's deleted and message removal if all channels are removed.
- Improved debug messages.

v1.7.9
----------------------
- :ref:`DirectMESSAGE` and :ref:`user` classes created for direct messaging.


