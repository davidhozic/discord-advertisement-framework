===============================
Functions
===============================

----------------------------
Tracing
----------------------------

trace
========================
.. autofunction:: daf.logging.tracing.trace


----------------------------
Getters
----------------------------

get_logger
========================
.. autofunction:: daf.logging.get_logger


get_client
========================
.. autofunction:: daf.client.get_client


get_guild_user
========================
.. autofunction:: daf.core.get_guild_user


get_shill_list
========================
.. autofunction:: daf.core.get_shill_list


----------------------------
Decorators
----------------------------

data_function
========================
.. autofunction:: daf.dtypes.data_function


----------------------------
Core control
----------------------------

initialize
========================
.. autofunction:: daf.core.initialize


shutdown
========================
.. autofunction:: daf.core.shutdown


run
========================
.. autofunction:: daf.core.run


----------------------------
Shilling list modification
----------------------------

add_object
========================
.. function:: daf.core.add_object(obj: Union[guild.USER, guild.GUILD]) -> None
    
    Adds a guild or an user to the daf.
    
    :Parameters:
        - obj: Union[guild.USER, guild.GUILD]
              The guild object to add into the daf.
    
    :Raises:
        - ValueError
              The guild/user is already added to the daf.
        - TypeError
              The object provided is not supported for addition.
        - TypeError
              Invalid parameter type.
        - Other
              Raised in the obj.initialize() method


add_object
========================
.. function:: daf.core.add_object(obj: Union[message.DirectMESSAGE, message.TextMESSAGE, message.VoiceMESSAGE],snowflake: Union[int, guild.GUILD, guild.USER, dc.Guild, dc.User, dc.Object]) -> None
    
    Adds a message to the daf.
    
    :Parameters:
        - obj: Union[message.DirectMESSAGE, message.TextMESSAGE, message.VoiceMESSAGE]
              The message object to add into the daf.
        - snowflake: Union[int, guild.GUILD, guild.USER, discord.Guild, discord.User]
              Which guild/user to add it to (can be snowflake id or a framework _BaseGUILD object or a discord API wrapper object).
    
    :Raises:
        - ValueError
              guild_id wasn't provided when adding a message object (to which guild should it add)
        - TypeError
              The object provided is not supported for addition.
        - TypeError
              Missing snowflake parameter.
        - ValueError
              Could not find guild with that id.
        - Other
              Raised in the obj.add_message() method


add_object
========================
.. function:: daf.core.add_object(obj: guild.AutoGUILD) -> None
    
    Adds a AutoGUILD to the shilling list.
    
    :Parameters:
        - obj: daf.guild.AutoGUILD
              AutoGUILD object that automatically finds guilds to shill in.
    
    :Raises:
        - TypeError
              The object provided is not supported for addition.
        - Other
              From :py:meth:`~daf.guild.AutoGUILD.initialize` method.


remove_object
========================
.. autofunction:: daf.core.remove_object

