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

   .. autoproperty:: created_at

USER
=====================
.. autoclass:: framework.guild.USER
   :members:

   .. autoproperty:: messages

   .. autoproperty:: snowflake

   .. autoproperty:: created_at

-----------------------------
Messages
-----------------------------

TextMESSAGE
=====================
.. autoclass:: framework.message.TextMESSAGE
    :members:

    .. autoproperty:: created_at

VoiceMESSAGE
=====================
.. autoclass:: framework.message.VoiceMESSAGE
    :members:

    .. autoproperty:: created_at


DirectMESSAGE
=====================
.. autoclass:: framework.message.DirectMESSAGE
    :members:

    .. autoproperty:: created_at


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
    See :ref:`relational database log (SQL)` for usage.

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

    DAF_SNOWFLAKE_NOT_FOUND:
        Value: 1

        Info: Guild with specified snowflake was not found (or user).

    DAF_USER_CREATE_DM:
        Value: 2

        Info: Was unable to create DM with user (probably user not found).

    DAF_YOUTUBE_STREAM_ERROR:
        Value: 3

        Info: The given youtube link could not be streamed (AUDIO, VoiceMESSAGE).

    DAF_FILE_NOT_FOUND:
        Value: 4

        Info: The given file was not found.

    DAF_SQL_CREATE_TABLES_ERROR:
        Value: 5

        Info: Unable to create all the tables.

    DAF_SQL_LOOKUPTABLE_NOT_FOUND:
        Value: 6

        Info: The lookup table was not found.

    DAF_SQL_BEGIN_ENGINE_ERROR:
        Value: 7

        Info: Unable to start engine.

    DAF_SQL_CR_LT_VALUES_ERROR:
        Value: 8

        Info: Unable to create lookuptables' rows.

    DAF_SQL_CREATE_DT_ERROR:
        Value: 9

        Info: Unable to create SQL data types.

    DAF_SQL_CREATE_VPF_ERROR:
        Value: 10

        Info: Unable to create views, procedures and functions.

    DAF_SQL_CURSOR_CONN_ERROR:
        Value: 11

        Info: Unable to connect the cursor.
