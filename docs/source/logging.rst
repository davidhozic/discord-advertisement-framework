====================
Logging
====================

.. |PK| replace:: **[Primary Key]**
.. |FK| replace:: **[Foreign Key]**


The framework allows to log sent messages for each :ref:`GUILD`/:ref:`USER` (if you set the "generate_log" to True inside the :ref:`GUILD` or :ref:`USER` object).
There are 2 different types of logs:

- Relational Database Log
- JSON file logs
    
Relational Database Log
================================
.. versionadded:: v1.9

This type of logging enables saving logs to a remote server inside the database. Currently **only Microsoft SQL server is supported.**.
In addition to being smaller in size, database logging takes up less space and it allows easier data analysis.

Usage
--------------------------------
To use a SQL base for logging, you need to pass the :ref:`run` function with the sql_manager parameter and pass it the LoggerSQL object.

.. literalinclude:: ../../Examples/Logging/SQL Logging/main_rickroll.py
    :language: python

Features
--------------------------------
+ Automatic creation of tables, procedures, functions, views, triggers
+ Caching for faster logging
+ Low redundancy for reduced file size
+ Automatic error recovery:
  
  - Automatic reconnect on disconnect - Retries 3 times in delays of 5 minutes, then switches to file logging
  - If tables are deleted, they are automatically recreated
  - If cached values get corrupted, they are automatically recached
  - If there are unhandable errors, the framework switches to file logging

.. note:: 

    The database must already exist! However it can be completely empty, no need to manually create the schema.

ER diagram of the logs
--------------------------------
.. image:: images/er_diagram.png
    :width: 500pt

Tables
--------------------------------

MessageLOG
~~~~~~~~~~~~~~~~~~~~
:Description:
    This table contains the actual logs of sent messages, if the message type is :ref:`DirectMESSAGE`, then all the information is stored in this table.
    If the types are **Voice/Text** MESSAGE, then part of the log (to which channels it sent), is saved in the :ref:`MessageChannelLOG` table.

:Attributes:
  - |PK| id: int  - This is an internal identificator of the log inside the database.
  - sent_data: int - Foreign key pointing to a row inside the :ref:`DataHISTORY` table.
  - message_type: int - Foreign key identificator pointing to a entry inside the :ref:`MessageTYPE` table.
  - guild_id: int -  Foreign key pointing to :ref:`GuildUSER` table.
  - message_mode: int - Foreign key pointing to :ref:`MessageMODE` table. This is non-null only for :ref:`DirectMESSAGE`.
  - dm_reason: str -  If MessageTYPE is not DirectMESSAGE or the send attempt was successful, this is NULL, otherwise it contains the string representation of the error that caused the message send attempt to be unsuccessful.
  - timestamp: datetime - The timestamp of the message send attempt.
  



DataHISTORY
~~~~~~~~~~~~~~~~~~~~
:Description:
    This table contains all the **different** data that was ever advertised. Every element is **unique** and is not replicated.
    This table exist to reduce reduncancy and file size of the logs whenever same data is advertised multiple times.
    When a log is created, it is first checked if the data sent was already sent before, if it was the id to the existing :ref:`DataHISTORY` row is used,
    else a new row is created.

:Attributes:
  - |PK| id: int - Internal identificator of data inside the database.
  - content: str -  Actual data that was sent.


MessageTYPE
~~~~~~~~~~~~~~~~~~~~
:Description:
    This is a lookup table containing the the different message types that exist within the framework (:ref:`Messages`).

:Attributes:
  - |PK| id: int - Internal identificator of the message type inside the database.
  - name: str - The name of the actual message type.

GuildUSER
~~~~~~~~~~~~~~~~~~~~
:Description:
    The table contains all the guilds/users the framework ever generated a log for.

:Attributes:
  - |PK| id: int - Internal identificator of the Guild/User inside the database.
  - snowflake_id: int - The discord (snowflake) identificator of the User/Guild
  - name: str - Name of the Guild/User
  - guild_type: int - Foreign key pointing to :ref:`GuildTYPE` table.


MessageMODE
~~~~~~~~~~~~~~~~~~~~
:Description:
    This is a lookup table containing the the different message modes available by :ref:`TextMESAGE` / :ref:`DirectMESSAGE`, it is set to null for :ref:`VoiceMESSAGE`.

:Attributes:
  - |PK| id: int - Internal identifier of the message mode inside the database.
  - name: str - The name of the actual message mode.



GuildTYPE
~~~~~~~~~~~~~~~~~~~~
:Description:
    This is a lookup table containing types of the guilds inside the framework (:ref:`Guilds (Servers)`).

:Attributes:
  - |PK| id: int -  Internal identifier of the guild type inside the database.
  - name: str - The name of the guild type.



CHANNEL
~~~~~~~~~~~~~~~~~~~~
:Description:
    The table contains all the channels that the framework ever advertised into.

:Attributes:
  - |PK| id: int - Internal identifier of the channel inside the database
  - snowflake_id: int - The discord (snowflake) identifier representing specific channel
  - name: str - The name of the channel
  - guild_id: int - Foreign key pointing to a row inside the :ref:`GuildUSER` table. It points to a guild that the channel is part of.


MessageChannelLOG
~~~~~~~~~~~~~~~~~~~~
:Description:
    Since messages can send into multiple channels, each MessageLOG has multiple channels which
    cannot be stored inside the :ref:`MessageLOG`.
    This is why this table exists. It contains channels of each :ref:`MessageLOG`.

:Attributes:
  - |PK| |FK| log_id: int ~ Foreign key pointing to a row inside :ref:`MessageLOG` (to which log this channel log belongs to).
  - |PK| |FK| channel_id  ~ Foreign key pointing to a row inside the :ref:`CHANNEL` table.


SQL custom data types
--------------------------------
This sections contains descriptions on all SQL data types that are user-defined.

t_tmp_channel_log
~~~~~~~~~~~~~~~~~~~~
:Description:
    This is only used in the :ref:`sp_save_log` procedure to accept a list of channels it was attempted to send into and the reason for failure.
    This is a custom table type that contains attributes:

:Attributes:
    - id: int ~ Internal DB id pointing to :ref:`CHANNEL` table.
    - reason: nvarchar ~ Reason why sending to the channel failed, if it was succeessful then this is NULL.



SQL Stored Procedures (SP)
--------------------------------

This section contains the description on all the saved procedures inside the SQL database.

sp_save_log
~~~~~~~~~~~~~~~~
.. code-block:: t-sql

    sp_save_log(@sent_data nvarchar(max),
            @message_type smallint,
            @guild_id int,
            @message_mode smallint,
            @dm_reason nvarchar(max),
            @channels t_tmp_channel_log READONLY

:Description:
    This procedure is used by the SQL python module to store the log instead of using SQLAlchemy for faster saving speed.

:Attributes:
    - sent_data: nvarchar -  The data that was sent (jsonized).
    - message_type: smallint - Internal DB id that points to :ref:`MessageTYPE` table.
    - guild_id: int ~ Internal DB id that points to :ref:`GuildUSER` table.
    - message_mode: smallint - Internal DB id that points to :ref:`MessageMODE` table.
    - dm_reason: nvarchar -  This can only be different from NULL if the type of message is DirectMESSAGE. In the case that the message type is :ref:`DirectMESSAGE`, then this attribute is different from NULL when the send attempt failed, if send attempt succeeded, then this is NULL.
    - channels: :ref:`t_tmp_channel_log` ~ Table Valued Parameter (TVP) - Holds channels it was advertised into, if message type is DirectMESSAGE, this is an empty table.


SQL User Defined Functions (UDF)
----------------------------------
This section contains the description on all user defined functions inside the SQL database.

fn_log_success_rate
~~~~~~~~~~~~~~~~~~~~
.. code-block:: t-sql

    fn_log_success_rate(@log_id int)

:Description:
    This UDF can only be used for logs that have channels, so logs that originated from :ref:`TextMESSAGE` or :ref:`VoiceMESSAGE`. The UDF calculates relative success of sent channels for a specific log entry (successful channels / all channels) which is a number between 0 and 1, 0 meaning no channels succeeded and 1 meaning all channels succeeded.



:Parameters:
  - log_id: int - The DB id of a certain log that is inside the database.

:Return:
    The UDF returns the success rate - a number of type ``decimal`` with 5 decimals of precision.

.. note:: 

    If the log_id is an id of a message log that has no channels, the UDF will return 1.


fn_guilduser_success_rate
~~~~~~~~~~~~~~~~~~~~~~~~~~
.. code-block:: t-sql
    
    fn_log_success_rate(@snowflake_id bigint, @limit int = 1000)

:Description:
    This UDF returns relative success rate for specific GUILD/USER based on the last few logs.
    Success rate is defined as (number of **fully** successful send attempts) / (number of all send attempts)

:Parameters:
  - snowflake_id: bigint ~ Discord's identificator (snowflake id) of the USER or GUILD you want to get the success rate for
  - limit: int ~ How many of the latest logs you want to use to calculate the relative success rate

:Return:
    The UDF returns the success rate ~ a number of type ``decimal`` with 5 decimals of precision.

.. note::
    
    If no logs exist for specific GUILD/USER, 1 is returned.


Views
----------------------------------
This section contains the description on all views inside the SQL database.

vMessageLogFullDETAIL
~~~~~~~~~~~~~~~~~~~~~~~~

:Description:
    The :ref:`MessageLOG` table contains mostly internal DB ids which makes it hard to see anything directly from it. This is why the :ref:`vMessageLogFullDETAIL` view exists. It contains all the information inside the MessageLOG table, but expanded with actual values and not just identificators making it easier to view the content of the log.



Triggers
----------------------------------
This section contains the description on all the triggers inside the SQL database.

tr_delete_msg_log
~~~~~~~~~~~~~~~~~~~

:Description:
    Entries in :ref:`MessageChannelLOG` get deleted if an entry inside :ref:`MessageLOG` gets deleted due to the :ref:`MessageChannelLOG` table having a cascading foreign key pointing to the :ref:`MessageLOG` table. However reverse is not the same, the :ref:`MessageLOG` table does not have anything pointing to the :ref:`MessageChannelLOG` table meaning that cascading based on foreign keys is not possible. 
    This trigger's job is to delete an entry inside the MessageLOG when all the entries in :ref:`MessageChannelLOG` referencing it get deleted. 


JSON Logging (file)
=============================================================
The logs are written in the JSON format and saved into a JSON file, that has the name of the guild or an user you were sending messages into.
The JSON files are fragmented by day and stored into folder ``Year/Month/Day``, this means that each day a new JSON file will be generated for that specific day for easier managing,
for example, if today is ``13.07.2022``, the log will be saved into the file that is located in 

.. code-block::

    History
    └───2022
    │   └───07
    │       └───13
    |           └─── #David's dungeon.json


Code Example
-----------------
.. literalinclude:: ../../Examples/Logging/JSON files/main_rickroll.py
    :language: python
    :caption: Code to produce JSON logs


Example of a log
------------------
.. literalinclude:: ../../Examples/Logging/JSON files/History/2022/05/23/#David's dungeon.json
    :language: python
    :caption: JSON file log