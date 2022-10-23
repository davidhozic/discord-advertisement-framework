=================
Sending messages
=================
This document holds information regarding shilling with message objects.

.. |TextMESSAGE| replace:: :class:`~daf.message.TextMESSAGE`
.. |VoiceMESSAGE| replace:: :class:`~daf.message.VoiceMESSAGE`
.. |DirectMESSAGE| replace:: :class:`~daf.message.DirectMESSAGE`
.. |GUILD| replace:: :class:`~daf.guild.GUILD`
.. |USER| replace:: :class:`~daf.guild.USER`


Guild types
-------------
Before you start sending any messages you need to define a |GUILD| / |USER|. object.
The |GUILD| objects represents Discord servers with text/voice channels and it can hold |TextMESSAGE|
and |VoiceMESSAGE| messages, while |USER| represents a single user on Discord and can hold |DirectMESSAGE| messages.
For more information about how to use |GUILD| / |USER| click on them.

Guilds can be passed to the framework at startup, see :ref:`quickstart` (``server_list``) for more info.


Message types
-----------------
Periodic messages can be represented with instances of **x**\ MESSAGE classes, where **x** represents the channel type.
The channel logic is merged with the message logic which is why there are 3 message classes you can create instances from.
These classes accept different parameters but still have some in common:

- ``start_period`` -  If not None, represents bottom range of randomized period 
- ``end_period`` - If ``start_period`` is not None, this represents upper range of randomized period, if ``start_period`` is None, represents fixed sending period.
- ``data`` (varies on message types) - data that is actually send to Discord.
- ``start_in``  - Defines when the message should be first shilled.
- ``remove_after`` - Defines when the message should be removed from Discord.

For more information about these, see |TextMESSAGE|, |VoiceMESSAGE|, |DirectMESSAGE|.

Text messages
~~~~~~~~~~~~~~~~~~
To periodically send text messages you'll have to use either |TextMESSAGE| for sending to text channels inside the guild or |DirectMESSAGE| for sending to user's private DM.
To add these messages to the guild, set the |GUILD| / |USER|'s ``messages`` parameter to a table that has the message objects inside.

The data that can be sent using this types of messages can be of type:

1. str (normal text, string)
2. :class:`~daf.dtypes.EMBED`
3. :class:`~daf.dtypes.FILE`
4. list containing data that is one of the first 3 types.
5. function on which the :class:`~daf.dtypes.data_function` was used (use for dynamically changeable data)

.. only:: html

    .. literalinclude:: ../../../Examples/Message Types/TextMESSAGE/main_send_string.py
        :language: Python
        :emphasize-lines: 8
        :caption: **TextMESSAGE example - normal text (string)**

    .. literalinclude:: ../../../Examples/Message Types/DirectMESSAGE/main_send_string.py
        :language: Python
        :emphasize-lines: 14
        :caption: **DirectMESSAGE example - normal text (string)**


Voice messages
~~~~~~~~~~~~~~~~~~
Shilling an audio message requires |VoiceMESSAGE| objects.
You can only stream audio to guilds, users(direct messages) are not supported.
You can either stream a fixed audio file or a youtube video, both thru :class:`daf.dtypes.AUDIO` object.

.. only:: html

    .. literalinclude:: ../../../Examples/Message Types/VoiceMESSAGE/main_stream_audio.py
        :emphasize-lines: 12
        :caption: **VoiceMESSAGE example - audio file**

The data that can be sent using this types of messages can be of type:

1. :class:`~daf.dtypes.AUDIO`
2. function on which the :class:`~daf.dtypes.data_function` was used (use for dynamically changeable data).