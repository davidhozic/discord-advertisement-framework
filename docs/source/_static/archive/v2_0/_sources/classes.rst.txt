=====================
Classes
=====================
This page contains information about any classes that can be used in the framework.


Guilds (Servers)
---------------------

GUILD
~~~~~~~~~~~~~~~~~~~~~
.. autoclass:: framework.GUILD
   :members:
   
   .. autoproperty:: messages

   .. autoproperty:: snowflake

USER
~~~~~~~~~~~~~~~~~~~~~
.. autoclass:: framework.USER
   :members:

   .. autoproperty:: messages

   .. autoproperty:: snowflake



Messages
---------------------

TextMESSAGE
~~~~~~~~~~~~~~~~~~~~~~~~~
.. autoclass:: framework.TextMESSAGE
    :members:

    .. autoproperty:: deleted

VoiceMESSAGE
~~~~~~~~~~~~~~~~~~~~~~~~~
.. autoclass:: framework.VoiceMESSAGE
    :members:

    .. autoproperty:: deleted

DirectMESSAGE
~~~~~~~~~~~~~~~~~~~~~~~~~
.. autoclass:: framework.DirectMESSAGE
    :members:

    .. autoproperty:: deleted




Message data types
---------------------
These classes describe data that can be passed to the :ref:`Messages` objects

EMBED
~~~~~~~~~~~~~~~~~~~~~~~~~
.. autoclass:: framework.EMBED
    :members:
    :exclude-members: Color, Colour

FILE
~~~~~~~~~~~~~~~~~~~~~~~~~
.. autoclass:: framework.FILE
    :members:

AUDIO
~~~~~~~~~~~~~~~~~~~~~~~~~
.. autoclass:: framework.AUDIO
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
.. note::
    See :ref:`Relational Database Log` for usage.

.. autoclass:: framework.LoggerSQL
    :members:
    :exclude-members: Base




Tracing
---------------------

TraceLEVELS
~~~~~~~~~~~~~~~~~~~~~~~~~
.. autoenum:: framework.TraceLEVELS
    :members:


Exceptions
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

    +----------------------------------------+------+----------------------------------------------------------------------------+
    | Name                                   | Code | Description                                                                |
    +----------------------------------------+------+----------------------------------------------------------------------------+
    | DAF_GUILD_ALREADY_ADDED                | 0    | Guild with specified snowflake is already added.                           |
    +----------------------------------------+------+----------------------------------------------------------------------------+
    | DAF_GUILD_ID_REQUIRED                  | 1    | Guild ID is required but was not passed.                                   |
    +----------------------------------------+------+----------------------------------------------------------------------------+
    | DAF_GUILD_ID_NOT_FOUND                 | 2    | Guild with specified snowflake was not found (or user).                    |
    +----------------------------------------+------+----------------------------------------------------------------------------+
    | DAF_USER_CREATE_DM                     | 3    | Was unable to create DM with user (probably user not found).               |
    +----------------------------------------+------+----------------------------------------------------------------------------+
    | DAF_INVALID_TYPE                       | 4    | Object of invalid type was given.                                          |
    +----------------------------------------+------+----------------------------------------------------------------------------+
    | DAF_YOUTUBE_STREAM_ERROR               | 5    | The given youtube link could not be streamed (AUDIO, VoiceMESSAGE).        |
    +----------------------------------------+------+----------------------------------------------------------------------------+
    | DAF_FILE_NOT_FOUND                     | 6    | The given file was not found.                                              |
    +----------------------------------------+------+----------------------------------------------------------------------------+
    | DAF_UPDATE_PARAMETER_ERROR             | 7    | The update method only accepts the following keyword arguments.            |
    +----------------------------------------+------+----------------------------------------------------------------------------+
    | DAF_MISSING_PARAMETER                  | 8    | The parameter(s) is(are) missing.                                          |
    +----------------------------------------+------+----------------------------------------------------------------------------+
    | DAF_SQL_CREATE_TABLES_ERROR            | 9    | Unable to create all the tables.                                           |
    +----------------------------------------+------+----------------------------------------------------------------------------+
    | DAF_SQL_LOOKUPTABLE_NOT_FOUND          | 10   | The lookup table was not found.                                            |
    +----------------------------------------+------+----------------------------------------------------------------------------+
    | DAF_SQL_BEGIN_ENGINE_ERROR             | 11   | Unable to start engine.                                                    |
    +----------------------------------------+------+----------------------------------------------------------------------------+
    | DAF_SQL_CR_LT_VALUES_ERROR             | 12   | Unable to create lookuptables' rows.                                       |
    +----------------------------------------+------+----------------------------------------------------------------------------+
    | DAF_SQL_CREATE_DT_ERROR                | 13   | Unable to create SQL data types.                                           |
    +----------------------------------------+------+----------------------------------------------------------------------------+
    | DAF_SQL_CREATE_VPF_ERROR               | 14   | Unable to create views, procedures and functions.                          |
    +----------------------------------------+------+----------------------------------------------------------------------------+
    | DAF_SQL_CURSOR_CONN_ERROR              | 15   | Unable to connect the cursor.                                              |
    +----------------------------------------+------+----------------------------------------------------------------------------+