Functions
======================
This page contains information about any functions that can be called.



add_object
--------------------------
.. function:: framework.core.add_object(obj: Union[USER, GUILD])
    :noindex:

    Adds a guild or an user to the framework.
    
    :Parameters:
        - obj: Union[:ref:`USER`, :ref:`GUILD`] - 
            The guild object to add into the framework.

    :Raises:
        - ValueError(code=DAF_GUILD_ALREADY_ADDED) -
            The guild/user is already added to the framework.
        - TypeError(code=DAF_INVALID_TYPE) - 
            The object provided is not supported for addition.
        - Other -
            Raised in the :ref:`Guilds (Servers)` ``.add_message()`` method

.. function:: framework.core.add_object(obj: Union[DirectMESSAGE, TextMESSAGE, VoiceMESSAGE], snowflake: Union[int, GUILD, USER, dc.Guild, dc.User])

    Adds a message to the framework.
    
    :Parameters:
        obj: Union[:ref:`DirectMESSAGE`, :ref:`TextMESSAGE`, :ref:`VoiceMESSAGE`]
            The message object to add into the framework.
        snowflake: Union[int, :ref:`GUILD`, :ref:`USER`, dc.Guild, dc.User]
            Which guild/user to add it to (can be snowflake id or a framework _BaseGUILD object or a discord API wrapper object).

    :Raises:
        TypeError(code=DAF_GUILD_ID_REQUIRED)
            guild_id wasn't provided when adding a message object (to which guild should it add)
        DAFNotFoundError(code=DAF_GUILD_ID_NOT_FOUND)
            Could not find guild with that id.
        TypeError(code=DAF_INVALID_TYPE)
            The object provided is not supported for addition.
        Other
            Raised in the :ref:`Guilds (Servers)` ``.add_message()`` method



data_function
--------------------------
.. autofunction:: framework.dtypes.data_function


get_client
--------------------------
.. autofunction:: framework.client.get_client


get_guild_user
--------------------------
.. autofunction:: framework.core.get_guild_user


get_sql_manager
--------------------------
.. autofunction:: framework.sql.get_sql_manager


remove_object
--------------------------
.. autofunction:: framework.core.remove_object


run
--------------------------
.. autofunction:: framework.core.run


shutdown
--------------------------
.. autofunction:: framework.core.shutdown


trace
--------------------------
.. autofunction:: framework.tracing.trace
