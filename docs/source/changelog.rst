Changelog
========================
.. seealso:: 
    `Releases <https://github.com/davidhozic/discord-advertisement-framework/releases>`_

.. note:: 
    The library first started as a single file script that I didn't make versios of.
    When I decided to turn it into a library, I've set the version number based on the amount of commits I have made since the start.

:v1.9.0:
    - Added support for logging into a SQL database (MS SQL Server only). See :ref:`relational database log`.
    - :ref:`run` function now accepts discord.Intents.
    - :ref:`add_object` and :ref:`remove_object` functions created to allow for dynamic modification of the shilling list.
    - Other small improvements.

:v1.8.1:
    - JSON file logging.
    - Automatic channel removal if channel get's deleted and message removal if all channels are removed.
    - Improved debug messages.

:v1.7.9: 
    - :ref:`DirectMESSAGE` and :ref:`user` classes for direct messaging.


