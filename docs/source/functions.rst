Functions
======================
This page contains information about any functions that can be called.



add_object
--------------------------
.. function:: framework.add_object(obj: Union[USER, GUILD])
    :noindex:

    Adds a guild or an user to the framework.
    
    :Parameters:
        - obj: Union[:ref:`USER`, :ref:`GUILD`] - 
            The guild object to add into the framework.

    :Raises:
        - DAFParameterError(code=DAF_GUILD_ALREADY_ADDED) -
            The guild/user is already added to the framework.
        - DAFParameterError(code=DAF_INVALID_TYPE) - 
            The object provided is not supported for addition.
        - Other -
            Raised in the :ref:`Guilds (Servers)` ``.add_message()`` method

.. function:: framework.add_object(obj: Union[DirectMESSAGE, TextMESSAGE, VoiceMESSAGE], snowflake: Union[int, GUILD, USER, dc.Guild, dc.User])

    Adds a message to the framework.
    
    :Parameters:
        obj: Union[:ref:`DirectMESSAGE`, :ref:`TextMESSAGE`, :ref:`VoiceMESSAGE`]
            The message object to add into the framework.
        snowflake: Union[int, :ref:`GUILD`, :ref:`USER`, dc.Guild, dc.User]
            Which guild/user to add it to (can be snowflake id or a framework _BaseGUILD object or a discord API wrapper object).

    :Raises:
        DAFParameterError(code=DAF_GUILD_ID_REQUIRED)
            guild_id wasn't provided when adding a message object (to which guild should it add)
        DAFNotFoundError(code=DAF_GUILD_ID_NOT_FOUND)
            Could not find guild with that id.
        DAFParameterError(code=DAF_INVALID_TYPE)
            The object provided is not supported for addition.
        Other
            Raised in the :ref:`Guilds (Servers)` ``.add_message()`` method

remove_object
--------------------------
.. function:: framework.remove_object(guild_id: int)
    :noindex:
    :async:

    Removes a guild from the framework that has the given guild_id.
    
    :Parameters:
        guild_id: int
            ID of the guild to remove.
    
    :Raises:
        - DAFNotFoundError(code=DAF_GUILD_ID_NOT_FOUND)
            Could not find guild with that id.
        - DAFParameterError(code=DAF_INVALID_TYPE)
            The object provided is not supported for removal.



.. function:: framework.remove_object(channel_ids: Iterable[int])
    :async:

    Removes messages that contain all the given channel ids.
    
    :Parameters:
        channel_ids: Iterable[int]
            The channel IDs that the message must have to be removed (it must have all of these).
    
    :Raises:
        DAFParameterError(code=DAF_INVALID_TYPE)
            The object provided is not supported for removal.



data_function
--------------------------
.. autofunction:: framework.data_function


get_client
--------------------------
.. autofunction:: framework.get_client


get_sql_manager
--------------------------
.. autofunction:: framework.get_sql_manager


run
--------------------------
.. autofunction:: framework.run


shutdown
--------------------------
.. autofunction:: framework.shutdown


trace
--------------------------
.. autofunction:: framework.trace


