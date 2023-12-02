====================
Logging (core)
====================

.. versionchanged:: v2.7

    Added **invite link tracking**


.. |PK| replace:: **[Primary Key]**
.. |FK| replace:: **[Foreign Key]**

The logging module is responsible for 2 types of logging:

1. **Messages** - Logs (attempts of) sent messages
2. **Invite links** - Tracks new member joins with configured invite links.

.. warning::

    To track invite links, the Members intent (event setting) is needed.
    To use invite link tracking, users need to enable the privileged intent 'SERVER MEMBERS INTENT' inside
    the Discord developer portal and also set the ``members`` intent to True
    inside the ``intents`` parameter of :class:`~daf.client.ACCOUNT`.

    Invites intent is also needed. Enable it by setting ``invites`` to True inside
    the ``intents`` parameter of :class:`~daf.client.ACCOUNT`.

    Invite link tracking is **bot account** only and does not work on user accounts.


Logging can be enabled for each :class:`~daf.guild.GUILD` / :class:`~daf.guild.USER` if the ``logging`` parameter is
set to ``True``.

.. note:: 
    
    **Invite links** will be tracked regardless of the GUILD's ``logging`` parameter. Invite link tracking is configured
    solely by the ``invite_track`` parameter inside :class:`~daf.guild.GUILD`.


Logging is handled thru so called **logging managers** and currently 3 exist:

- LoggerJSON: (default) Logging into JSON files. (:ref:`JSON Logging (file)`)
- LoggerSQL:  Logging into a relational database (local or remote). (:ref:`Relational Database Log (SQL)`)
- LoggerCSV:  Logging into CSV files, where certain fields are still JSON. (:ref:`CSV Logging (file)`)

Each logging manager can have a backup manager specified by it's ``fallback`` parameter.
If current manager fails, it's fallback manager will be used temporarily to store the log.
It will only use the fallback once and then, at the next logging attempt, the original manager will be used.

.. figure:: ./images/logging_process.drawio.svg
    
    Logging process with fallback


JSON Logging (file)
=========================
The logs are written in the JSON format and saved into a JSON file, that has the name of the guild / user you were sending messages into.
The JSON files are grouped by day and stored into folder ``Year/Month/Day``, this means that each day a new JSON file will be generated for that specific day for easier managing,
for example, if today is ``13.07.2022``, the log will be saved into the file that is located in 

.. code-block::

    History
    └───2022
    │   └───07
    │       └───13
    |           └─── #David's dungeon.json


JSON structure
------------------
The log structure is the same for both :class:`~daf.guild.USER` and :class:`~daf.guild.GUILD`.
All logs will contain keys:

- "name": The name of the guild/user
- "id": Snowflake ID of the guild/user
- "type": object type (GUILD/USER) that generated the log.
- "invite_tracking": Dictionary that holds invite link tracking information.
  
  It's keys are invite link ID's (final part of invite link URL) and the value is a list of invite link logs, where
  a new log is created on each member join.
  
  Each invite log is a dictionary and contains the following keys:

  - "id": Member's snowflake (Discord) ID,
  - "name": Member's username,
  - "index": serial number of the log,
  - "timestamp": Date-Time when the log was created.

- "message_tracking": Dictionary that holds information about sent messages.

  .. note:: Only messages sent from DAF are tracked. Other messages are not tracked.
  
  The keys are snowflake IDs of each each account who has sent the message from DAF.
  
  The value under each key is a dictionary containing: 

  - "name": Name of the sender (author)
  - "id": Snowflake ID of the sender
  - "messages": List of previously sent messages by the corresponding author with their context.
    It is message type dependent and is generated in:
   
    + :py:meth:`daf.message.TextMESSAGE.generate_log_context`
    + :py:meth:`daf.message.VoiceMESSAGE.generate_log_context`
    + :py:meth:`daf.message.DirectMESSAGE.generate_log_context`

.. seealso::
    :download:`Example structure <./DEP/David's py dungeon.json>`

.. only:: html

    JSON code example
    -----------------
    .. literalinclude:: ./DEP/main_rickroll.py
        :language: python
        :caption: Code to produce JSON logs
        



CSV Logging (file)
=========================
The logs are written in the CSV format and saved into a CSV file, that has the name of the guild or an user you were sending messages into.
The CSV files are fragmented by day and stored into folder ``Year/Month/Day``, this means that each day a new CSV file will be generated for that specific day for easier managing,
for example, if today is ``13.07.2023``, the log will be saved into the file that is located in 

.. code-block::

    History
    └───2023
    │   └───07
    │       └───13
    |           └─── #David's dungeon.csv


CSV structure
------------------

.. warning:: **Invite link** tracking is not supported with CSV logging.

The structure contains the following attributes:

- Index (integer) - this is a unique ID,
- Timestamp (string)
- Guild Type (string),
- Guild Name (string),
- Guild Snowflake (integer),
- Author name (string),
- Author Snowflake (integer),
- Message Type (string),
- Sent Data (json),
- Message Mode (non-empty for :class:`~daf.message.TextMESSAGE` and :class:`~daf.message.DirectMESSAGE`) (string),
- Message Channels (non-empty for :class:`~daf.message.TextMESSAGE` and :class:`~daf.message.VoiceMESSAGE`) (json),
- Success Info (non-empty for :class:`~daf.message.DirectMESSAGE`) (json),


.. note::
    Attributes marked with ``(json)`` are the same as in :ref:`JSON Logging (file)`

.. seealso::
    :download:`Structure example <./DEP/David's py dungeon.csv>`


.. only:: html

    CSV code example
    -----------------
    .. literalinclude:: ./DEP/main_rickroll.py
        :language: python
        :caption: Code to produce JSON logs
        





Relational Database Log (SQL)
================================
This type of logging enables saving logs to a remote server inside the database.
In addition to being smaller in size, database logging takes up less space and it allows easier data analysis.


Dialects
----------------------
The dialect is selected via the ``dialect`` parameter in :class:`~daf.logging.sql.LoggerSQL`.
The following dialects are supported:

- Microsoft SQL Server
- PostgreSQL
- SQLite,
- MySQL


Usage
--------------------------------
For daf to use SQL logging, you need to pass the :func:`~daf.core.run` function with the ``logger`` parameter and pass it the :class:`~daf.logging.sql.LoggerSQL` object.

.. only:: html

    .. literalinclude:: ./DEP/rolls.py
        :language: python
        

Features
--------------------------------
- Multiple dialects (sqlite, mssql, postgresql, mysql)
- Automatic creation of the schema
- Caching for faster logging
- Low redundancy for reduced file size
- Automatic error recovery

.. warning:: 

    The database must already exist (unless using SQLite).
    However it can be completely empty, no need to manually create the schema.


ER diagram
--------------------------------
.. image:: ./DEP/sql_er.drawio.svg
    :width: 1440


Analysis
-------------------------------
The :class:`~daf.logging.sql.LoggerSQL` provides some methods for data analysis:

- For message history:

  - :py:meth:`~daf.logging.sql.LoggerSQL.analytic_get_num_messages`
  - :py:meth:`~daf.logging.sql.LoggerSQL.analytic_get_message_log`

- For invite link tracking:

  - :py:meth:`~daf.logging.sql.LoggerSQL.analytic_get_num_invites`
  - :py:meth:`~daf.logging.sql.LoggerSQL.analytic_get_invite_log`





SQL Tables
--------------------------------

MessageLOG
~~~~~~~~~~~~~~~~~~~~
:Description:
    This table contains the actual logs of sent messages, if the message type is :ref:`DirectMESSAGE`, then all the information is stored in this table.
    If the types are **Voice/Text** MESSAGE, then channel part of the log is saved in the :ref:`MessageChannelLOG` table.

:Attributes:
  - |PK| id: Integer  - This is an internal ID of the log inside the database.
  - sent_data: Integer - Foreign key pointing to a row inside the :ref:`DataHISTORY` table.
  - message_type: SmallInteger - Foreign key ID pointing to a entry inside the :ref:`MessageTYPE` table.
  - guild_id: Integer -  Foreign key pointing to :ref:`GuildUSER` table, represents guild id of guild the message was sent into.
  - author_id: Integer -  Foreign key pointing to :ref:`GuildUSER` table, represents the author account of the message.
  - message_mode: SmallInteger - Foreign key pointing to :ref:`MessageMODE` table. This is non-null only for :ref:`DirectMESSAGE`.
  - dm_reason: String -  If MessageTYPE is not DirectMESSAGE or the send attempt was successful, this is NULL, otherwise it contains the string representation of the error that caused the message send attempt to be unsuccessful.
  - timestamp: DateTime - The timestamp of the message send attempt.
  

DataHISTORY
~~~~~~~~~~~~~~~~~~~~
:Description:
    This table contains all the **different** data that was ever advertised. Every element is **unique** and is not replicated.
    This table exist to reduce redundancy and file size of the logs whenever same data is advertised multiple times.
    When a log is created, it is first checked if the data sent was already sent before, if it was the id to the existing :ref:`DataHISTORY` row is used,
    else a new row is created.

:Attributes:
  - |PK| id: Integer - Internal ID of data inside the database.
  - content: JSON -  Actual data that was sent.


MessageTYPE
~~~~~~~~~~~~~~~~~~~~
:Description:
    This is a lookup table containing the the different message types that exist within the framework (:ref:`Messages`).

:Attributes:
  - |PK| id: SmallInteger - Internal ID of the message type inside the database.
  - name: String - The name of the actual message type.

GuildUSER
~~~~~~~~~~~~~~~~~~~~
:Description:
    The table contains all the guilds/users the framework ever generated a log for and all the authors.

:Attributes:
  - |PK| id: Integer - Internal ID of the Guild/User inside the database.
  - snowflake_id: BigInteger - The discord (snowflake) ID of the User/Guild
  - name: String - Name of the Guild/User
  - guild_type: SmallInteger - Foreign key pointing to :ref:`GuildTYPE` table.


MessageMODE
~~~~~~~~~~~~~~~~~~~~
:Description:
    This is a lookup table containing the the different message modes available by :ref:`TextMESSAGE` / :ref:`DirectMESSAGE`, it is set to null for :ref:`VoiceMESSAGE`.

:Attributes:
  - |PK| id: SmallInteger - Internal identifier of the message mode inside the database.
  - name: String - The name of the actual message mode.



GuildTYPE
~~~~~~~~~~~~~~~~~~~~
:Description:
    This is a lookup table containing types of the guilds inside the framework (:ref:`Guilds`).

:Attributes:
  - |PK| id: SmallInteger -  Internal identifier of the guild type inside the database.
  - name: String - The name of the guild type.



CHANNEL
~~~~~~~~~~~~~~~~~~~~
:Description:
    The table contains all the channels that the framework ever advertised into.

:Attributes:
  - |PK| id: Integer - Internal identifier of the channel inside the database
  - snowflake_id: BigInteger - The discord (snowflake) identifier representing specific channel
  - name: String - The name of the channel
  - guild_id: Integer - Foreign key pointing to a row inside the :ref:`GuildUSER` table. It points to a guild that the channel is part of.


MessageChannelLOG
~~~~~~~~~~~~~~~~~~~~
:Description:
    Since messages can send into multiple channels, each MessageLOG has multiple channels which
    cannot be stored inside the :ref:`MessageLOG`.
    This is why this table exists. It contains channels of each :ref:`MessageLOG`.

:Attributes:
  - |PK| |FK| log_id: Integer - Foreign key pointing to a row inside :ref:`MessageLOG` (to which log this channel log belongs to).
  - |PK| |FK| channel_id: Integer  - Foreign key pointing to a row inside the :ref:`CHANNEL` table.
  - reason: String - Reason why the send failed or ``NULL`` if send succeeded.


Invite
~~~~~~~~~~~~~~~~~~~~
:Description:
    Table that represents tracked invite links.

:Attributes:
  - |PK| id: Integer - Internal ID of the invite inside the database.
  - |FK| guild_id: Integer  - Foreign key pointing to a row inside the :ref:`GuildUSER` table (The guild that owns the invite).
  - discord_id: String - Discord's invite ID (final part of the invite URL).


InviteLOG
~~~~~~~~~~~~~~~~~~~~
:Description:
    Table which's entries are logs of member joins into a guild using a specific invite link.

:Attributes:
  - |PK| id: Integer - Internal ID of the log inside the database.
  - |FK| invite_id: Integer  - Foreign key pointing to a row inside the :ref:`Invite` table. Describes the link member used to join a guild.
  - |FK| member_id: Integer - Foreign key pointing to a row inside the :ref:`GuildUSER` table. Describes the member who joined.
  - timestamp: DateTime - The date and time a member joined into a guild.
