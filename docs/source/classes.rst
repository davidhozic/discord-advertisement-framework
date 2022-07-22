=====================
Classes
=====================
This page contains infomation about any classes that can be used in the framework.


Guilds (Servers)
---------------------

GUILD
~~~~~~~~~~~~~~~~~~~~~
.. autoclass:: framework.GUILD
   :members:

USER
~~~~~~~~~~~~~~~~~~~~~
.. autoclass:: framework.USER
   :members:




Messages
---------------------

TextMESSAGE
~~~~~~~~~~~~~~~~~~~~~~~~~
.. autoclass:: framework.TextMESSAGE
    :members:

VoiceMESSAGE
~~~~~~~~~~~~~~~~~~~~~~~~~
.. autoclass:: framework.VoiceMESSAGE
    :members:

DirectMESSAGE
~~~~~~~~~~~~~~~~~~~~~~~~~
.. autoclass:: framework.DirectMESSAGE
    :members:




Message data types
---------------------

EMBED
~~~~~~~~~~~~~~~~~~~~~~~~~
.. autoclass:: framework.EMBED
    :members:

FILE
~~~~~~~~~~~~~~~~~~~~~~~~~
.. autoclass:: framework.FILE
    :members:

AUDIO
~~~~~~~~~~~~~~~~~~~~~~~~~
.. autoclass:: framework.AUDIO
    :members:

FunctionBaseCLASS
~~~~~~~~~~~~~~~~~~~~~~~~~
.. autoclass:: framework.FunctionBaseCLASS
    :members:




Clients
---------------------

CLIENT
~~~~~~~~~~~~~~~~~~~~~~~~~
.. autoclass:: framework.CLIENT
    :members:




SQL
---------------------

LoggerSQL
~~~~~~~~~~~~~~~~~~~~~~~~~
.. autoclass:: framework.LoggerSQL
    :members:




Tracing
---------------------

TraceLEVELS
~~~~~~~~~~~~~~~~~~~~~~~~~
.. autoclass:: framework.TraceLEVELS
    :members:




Exceptions (Classes)
---------------------

Types
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    **DAFError**

    .. autoclass:: framework.DAFError
       :members:

    **DAFSQLError**

    .. autoclass:: framework.DAFSQLError
        :members:


    **DAFNotFoundError**

    .. autoclass:: framework.DAFNotFoundError
        :members:

    **DAFParameterError**

    .. autoclass:: framework.DAFParameterError
        :members:


Error codes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    **DAF_GUILD_ALREADY_ADDED**
        :Enumerated value:
            0

        :Description:
            Guild with specified snowflake is already added.

 
    **DAF_GUILD_ID_REQUIRED**
        :Enumerated value:
            1

        :Description:
            Guild ID is required but was not passed.

 
    **DAF_GUILD_ID_NOT_FOUND**
        :Enumerated value:
            2

        :Description:
            Guild with specified snowflake was not found (or user).

 
    **DAF_USER_CREATE_DM**
        :Enumerated value:
            3

        :Description:
            Was unble to create DM with user (probably user not found).

 
    **DAF_INVALID_TYPE**
        :Enumerated value:
            4

        :Description:
            Object of invalid type was given.

 
    **DAF_YOUTUBE_STREAM_ERROR**
        :Enumerated value:
            5

        :Description:
            The given youtube link could not be streamed (AUDIO, VoiceMESSAGE).

 
    **DAF_FILE_NOT_FOUND**
        :Enumerated value:
            6

        :Description:
            The given file was not found.

 
    **DAF_UPDATE_PARAMETER_ERROR**
        :Enumerated value:
            7

        :Description:
            The update method only accepts the following keyword arguments.

 
    **DAF_MISSING_PARAMETER**
        :Enumerated value:
            8

        :Description:
            The parameter(s) is(are) missing.

 
    **DAF_SQL_CREATE_TABLES_ERROR**
        :Enumerated value:
            9

        :Description:
            Unable to create all the tables.

 
    **DAF_SQL_LOOKUPTABLE_NOT_FOUND**
        :Enumerated value:
            10

        :Description:
            The lookup table was not found.

 
    **DAF_SQL_BEGIN_ENGINE_ERROR**
        :Enumerated value:
            11

        :Description:
            Unable to start engine.

 
    **DAF_SQL_CR_LT_VALUES_ERROR**
        :Enumerated value:
            12

        :Description:
            Unable to create lookuptables' rows.

 
    **DAF_SQL_CREATE_DT_ERROR**
        :Enumerated value:
            13

        :Description:
            Unable to create SQL data types.

 
    **DAF_SQL_CREATE_VPF_ERROR**
        :Enumerated value:
            14

        :Description:
            Unable to create views, procedures and functions.

 
    **DAF_SQL_CURSOR_CONN_ERROR**
        :Enumerated value:
            15

        :Description:
            Unable to connect the cursor.

