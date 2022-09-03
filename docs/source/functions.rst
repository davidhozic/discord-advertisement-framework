======================
Functions
======================
This page contains information about any functions that can be called.

------------------------------
Shilling list modification
------------------------------

add_object
=======================
.. function:: daf.core.add_object(obj: Union[USER, GUILD])
    :noindex:

    Adds a guild or an user to the daf.
    
    :Parameters:
        - obj: Union[:ref:`USER`, :ref:`GUILD`] - 
            The guild object to add into the daf.

    :Raises:
        - ValueError -
            The guild/user is already added to the daf.
        - TypeError- 
            The object provided is not supported for addition.
        - Other -
            Raised in the :ref:`Guilds (Servers)` ``.add_message()`` method

.. function:: daf.core.add_object(obj: Union[DirectMESSAGE, TextMESSAGE, VoiceMESSAGE], snowflake: Union[int, GUILD, USER, dc.Guild, dc.User])

    Adds a message to the daf.
    
    :Parameters:
        obj: Union[:ref:`DirectMESSAGE`, :ref:`TextMESSAGE`, :ref:`VoiceMESSAGE`]
            The message object to add into the daf.
        snowflake: Union[int, :ref:`GUILD`, :ref:`USER`, dc.Guild, dc.User]
            Which guild/user to add it to (can be snowflake id or a framework _BaseGUILD object or a discord API wrapper object).

    :Raises:
        TypeError
            guild_id wasn't provided when adding a message object (to which guild should it add)
        DAFNotFoundError(code=DAF_SNOWFLAKE_NOT_FOUND)
            Could not find guild with that id.
        TypeError
            The object provided is not supported for addition.
        Other
            Raised in the :ref:`Guilds (Servers)` ``.add_message()`` method


remove_object
=======================
.. autofunction:: daf.core.remove_object



-------------------------
Getters
-------------------------

get_client
=======================
.. autofunction:: daf.client.get_client


get_guild_user
=======================
.. autofunction:: daf.core.get_guild_user


get_shill_list
=======================
.. autofunction:: daf.core.get_shill_list


get_sql_manager
=======================
.. autofunction:: daf.sql.get_sql_manager


------------------------------
Decorators
------------------------------

data_function
=======================
.. autofunction:: daf.dtypes.data_function



--------------------------------
Core controls
--------------------------------
run
=======================
.. autofunction:: daf.core.run


shutdown
=======================
.. autofunction:: daf.core.shutdown


--------------------------------
Debug
--------------------------------

trace
=======================
.. autofunction:: daf.tracing.trace