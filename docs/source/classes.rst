
===============================
Classes
===============================

----------------------------
Tracing
----------------------------

TraceLEVELS
========================
.. autoenum:: daf.logging.tracing.TraceLEVELS
    :members:


----------------------------
Logging related
----------------------------

LoggerBASE
========================
.. autoclass:: daf.logging.LoggerBASE
    :members:

    


LoggerCSV
========================
.. autoclass:: daf.logging.LoggerCSV
    :members:

    


LoggerJSON
========================
.. autoclass:: daf.logging.LoggerJSON
    :members:

    


LoggerSQL
========================
.. autoclass:: daf.logging.sql.LoggerSQL
    :members:

    


----------------------------
Exceptions
----------------------------

DAFError
========================
.. autoclass:: daf.exceptions.DAFError
    :members:

    


DAFNotFoundError
========================
.. autoclass:: daf.exceptions.DAFNotFoundError
    :members:

    


DAFSQLError
========================
.. autoclass:: daf.exceptions.DAFSQLError
    :members:

    
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

    DAF_SQL_BEGIN_ENGINE_ERROR:
        Value: 7

        Info: Unable to start engine.

    DAF_SQL_CR_LT_VALUES_ERROR:
        Value: 8

        Info: Unable to create lookuptables' rows.

    DAF_SQL_SAVE_LOG_ERROR:
        Value: 12

        Info: Unable to save the log to SQL


----------------------------
Message data types
----------------------------

EMBED
========================
.. autoclass:: daf.dtypes.EMBED
    :members:
    :exclude-members: Colour, Color


FILE
========================
.. autoclass:: daf.dtypes.FILE
    :members:

    


AUDIO
========================
.. autoclass:: daf.dtypes.AUDIO
    :members:

    


----------------------------
Messages
----------------------------

TextMESSAGE
========================
.. autoclass:: daf.message.TextMESSAGE
    :members:

    .. autoproperty:: daf.message.TextMESSAGE.created_at


DirectMESSAGE
========================
.. autoclass:: daf.message.DirectMESSAGE
    :members:

    .. autoproperty:: daf.message.DirectMESSAGE.created_at


VoiceMESSAGE
========================
.. autoclass:: daf.message.VoiceMESSAGE
    :members:

    .. autoproperty:: daf.message.VoiceMESSAGE.created_at


----------------------------
Guilds
----------------------------

GUILD
========================
.. autoclass:: daf.guild.GUILD
    :members:

    .. autoproperty:: daf.guild.GUILD.created_at

    .. autoproperty:: daf.guild.GUILD.messages

    .. autoproperty:: daf.guild.GUILD.snowflake


USER
========================
.. autoclass:: daf.guild.USER
    :members:

    .. autoproperty:: daf.guild.USER.created_at

    .. autoproperty:: daf.guild.USER.messages

    .. autoproperty:: daf.guild.USER.snowflake

