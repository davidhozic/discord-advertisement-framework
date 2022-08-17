=====================
Classes
=====================
This page contains information about any classes that can be used in the framework.

-----------------------------
Guilds (Servers)
-----------------------------

GUILD
=====================
.. autoclass:: framework.guild.GUILD
   :members:
   
   .. autoproperty:: messages

   .. autoproperty:: snowflake

USER
=====================
.. autoclass:: framework.guild.USER
   :members:

   .. autoproperty:: messages

   .. autoproperty:: snowflake


-----------------------------
Messages
-----------------------------

TextMESSAGE
=====================
.. autoclass:: framework.message.TextMESSAGE
    :members:

    .. autoproperty:: deleted

VoiceMESSAGE
=====================
.. autoclass:: framework.message.VoiceMESSAGE
    :members:

    .. autoproperty:: deleted

DirectMESSAGE
=====================
.. autoclass:: framework.message.DirectMESSAGE
    :members:

    .. autoproperty:: deleted



-----------------------------
Message data types
-----------------------------
These classes describe data that can be passed to the :ref:`Messages` objects

EMBED
=====================
.. autoclass:: framework.dtypes.EMBED
    :members:
    :exclude-members: Color, Colour

FILE
=====================
.. autoclass:: framework.dtypes.FILE
    :members:

AUDIO
=====================
.. autoclass:: framework.dtypes.AUDIO
    :members:



-----------------------------
Clients
-----------------------------

CLIENT
=====================
.. autoclass:: framework.client.CLIENT
    :members:

    .. autoproperty:: framework.client.CLIENT.guilds

    .. autoproperty:: framework.client.CLIENT.private_channels
        
    .. autoproperty:: framework.client.CLIENT.user


-----------------------------
SQL
-----------------------------

LoggerSQL
=====================
.. note::
    See :ref:`Relational Database Log` for usage.

.. autoclass:: framework.sql.LoggerSQL
    :members:
    :exclude-members: Base



-----------------------------
Tracing
-----------------------------

TraceLEVELS
=====================
.. autoenum:: framework.tracing.TraceLEVELS
    :members:


-----------------------------
Exceptions
-----------------------------

Types
=====================

DAFError
------------------------

.. autoclass:: framework.exceptions.DAFError
    :members:

DAFSQLError
------------------------

.. autoclass:: framework.exceptions.DAFSQLError
    :members:


DAFNotFoundError
------------------------

.. autoclass:: framework.exceptions.DAFNotFoundError
    :members:


Error codes
=====================
.. Caution::
    The error code's number can change when a new version is released.
    If you want to check if an exception has a certain code, use the constant name instead.

.. glossary::

    DAF_GUILD_ALREADY_ADDED:
        Value: 0

        Info: Guild with specified snowflake is already added.

    DAF_GUILD_ID_REQUIRED:
        Value: 1

        Info: Guild ID is required but was not passed.

    DAF_GUILD_ID_NOT_FOUND:
        Value: 2

        Info: Guild with specified snowflake was not found (or user).

    DAF_USER_CREATE_DM:
        Value: 3

        Info: Was unable to create DM with user (probably user not found).

    DAF_YOUTUBE_STREAM_ERROR:
        Value: 5

        Info: The given youtube link could not be streamed (AUDIO, VoiceMESSAGE).

    DAF_FILE_NOT_FOUND:
        Value: 6

        Info: The given file was not found.

    DAF_MISSING_PARAMETER:
        Value: 7

        Info: The parameter(s) is(are) missing.

    DAF_CHANNEL_GUILD_MISMATCH_ERROR:
        Value: 8

        Info: The channel with given ID does not belong into this guild but is part of a different guild.

    DAF_SQL_CREATE_TABLES_ERROR:
        Value: 9

        Info: Unable to create all the tables.

    DAF_SQL_LOOKUPTABLE_NOT_FOUND:
        Value: 10

        Info: The lookup table was not found.

    DAF_SQL_BEGIN_ENGINE_ERROR:
        Value: 11

        Info: Unable to start engine.

    DAF_SQL_CR_LT_VALUES_ERROR:
        Value: 12

        Info: Unable to create lookuptables' rows.

    DAF_SQL_CREATE_DT_ERROR:
        Value: 13

        Info: Unable to create SQL data types.

    DAF_SQL_CREATE_VPF_ERROR:
        Value: 14

        Info: Unable to create views, procedures and functions.

    DAF_SQL_CURSOR_CONN_ERROR:
        Value: 15

        Info: Unable to connect the cursor.
