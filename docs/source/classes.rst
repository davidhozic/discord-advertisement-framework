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
.. table:: 
    :align: left
    :name: error_codes

    +------+----------------------------------------------------------------------------+
    | 0    | Guild with specified snowflake is already added.                           |
    +------+----------------------------------------------------------------------------+
    | 1    | Guild ID is required but was not passed.                                   |
    +------+----------------------------------------------------------------------------+
    | 2    | Guild with specified snowflake was not found (or user).                    |
    +------+----------------------------------------------------------------------------+
    | 3    | Was unble to create DM with user (probably user not found).                |
    +------+----------------------------------------------------------------------------+
    | 4    | Object of invalid type was given.                                          |
    +------+----------------------------------------------------------------------------+
    | 5    | The given youtube link could not be streamed (AUDIO, VoiceMESSAGE).        |
    +------+----------------------------------------------------------------------------+
    | 6    | The given file was not found.                                              |
    +------+----------------------------------------------------------------------------+
    | 7    | The update method only accepts the following keyword arguments.            |
    +------+----------------------------------------------------------------------------+
    | 8    | The parameter(s) is(are) missing.                                          |
    +------+----------------------------------------------------------------------------+
    | 9    | Unable to create all the tables.                                           |
    +------+----------------------------------------------------------------------------+
    | 10   | The lookup table was not found.                                            |
    +------+----------------------------------------------------------------------------+
    | 11   | Unable to start engine.                                                    |
    +------+----------------------------------------------------------------------------+
    | 12   | Unable to create lookuptables' rows.                                       |
    +------+----------------------------------------------------------------------------+
    | 13   | Unable to create SQL data types.                                           |
    +------+----------------------------------------------------------------------------+
    | 14   | Unable to create views, procedures and functions.                          |
    +------+----------------------------------------------------------------------------+
    | 15   | Unable to connect the cursor.                                              |
    +------+----------------------------------------------------------------------------+