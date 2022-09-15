======================
Functions
======================
This page contains information about any functions that can be called.



------------------------
Tracing
------------------------

trace
========================
.. autofunction:: daf.logging.tracing.trace


------------------------
Getters
------------------------

get_logger
========================
.. autofunction:: daf.logging.logging.get_logger


get_client
========================
.. autofunction:: daf.client.get_client


get_guild_user
========================
.. autofunction:: daf.core.get_guild_user


get_shill_list
========================
.. autofunction:: daf.core.get_shill_list


------------------------
Decorators
------------------------

data_function
========================
.. autofunction:: daf.dtypes.data_function


------------------------
Core control
------------------------

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
.. function:: daf.core.add_object(obj: typing.Union[daf.guild.USER, daf.guild.GUILD])
    
    Adds a guild or an user to the daf.
	
	:Parameters:
	    obj: Union[guild.USER, guild.GUILD]
	        The guild object to add into the daf.
	
	:Raises:
	    ValueError
	        The guild/user is already added to the daf.
	    TypeError
	        The object provided is not supported for addition.
	    TypeError
	        Invalid parameter type.
	    Other
	        Raised in the obj.initialize() method

.. function:: daf.core.add_object(obj: typing.Union[daf.message.text_based.DirectMESSAGE, daf.message.text_based.TextMESSAGE, daf.message.voice_based.VoiceMESSAGE],snowflake: typing.Union[int, daf.guild.GUILD, daf.guild.USER, _discord.guild.Guild, _discord.user.User, _discord.object.Object])
    
    Adds a message to the daf.
	
	:Parameters:
	    obj: Union[message.DirectMESSAGE, message.TextMESSAGE, message.VoiceMESSAGE]
	        The message object to add into the daf.
	    snowflake: Union[int, guild.GUILD, guild.USER, dc.Guild, dc.User]
	        Which guild/user to add it to (can be snowflake id or a framework _BaseGUILD object or a discord API wrapper object).
	
	:Raises:
	    ValueError
	        guild_id wasn't provided when adding a message object (to which guild should it add)
	    TypeError
	        The object provided is not supported for addition.
	    TypeError
	        Missing snowflake parameter.
	    DAFNotFoundError(code=DAF_SNOWFLAKE_NOT_FOUND)
	        Could not find guild with that id.
	    Other
	        Raised in the obj.add_message() method


remove_object
========================
.. autofunction:: daf.core.remove_object

