
----------------------------
Shilling list modification
----------------------------

add_object
========================
.. function:: daf.core.add_object(obj: <class 'daf.client.ACCOUNT'>) -> None
    
    Adds an account to the framework.
    
    
    :param obj: The account object to add
    :type obj: client.ACCOUNT
    
    
    :raises ValueError: The account has already been added to the list.
    :raises TypeError: ``obj`` is of invalid type.


add_object
========================
.. function:: daf.core.add_object(obj: typing.Union[daf.guild.USER, daf.guild.GUILD, daf.guild.AutoGUILD],snowflake: <class 'daf.client.ACCOUNT'>) -> None
    
    Adds a guild or an user to the daf.
    
    
    :param obj: The guild object to add into the account (``snowflake``).
    :type obj: guild.USER | guild.GUILD | guild.AutoGUILD
    :param snowflake: The account to add this guild/user to.
    :type snowflake: client.ACCOUNT=None
    
    
    :raises ValueError: The guild/user is already added to the daf.
    :raises TypeError: The object provided is not supported for addition.
    :raises TypeError: Invalid parameter type.
    :raises RuntimeError: When using deprecated method of adding items to the shill list,
        no accounts were available.
    :raises Other: Raised in the obj.initialize() method


add_object
========================
.. function:: daf.core.add_object(obj: typing.Union[daf.message.text_based.DirectMESSAGE, daf.message.text_based.TextMESSAGE, daf.message.voice_based.VoiceMESSAGE],snowflake: typing.Union[int, daf.guild.GUILD, daf.guild.USER]) -> None
    
    Adds a message to the daf.
    
    
    :param obj: The message object to add into the daf.
    :type obj: message.DirectMESSAGE | message.TextMESSAGE | message.VoiceMESSAGE
    :param snowflake: Which guild/user to add it to (can be snowflake id or a framework _BaseGUILD object or a discord API wrapper object).
    :type snowflake: int | guild.GUILD | guild.USER | discord.Guild | discord.User | discord.Object
    
    
    :raises TypeError: The object provided is not supported for addition.
    :raises ValueError: guild_id wasn't provided when adding a message object (to which guild should it add)
    :raises ValueError: Missing snowflake parameter.
    :raises ValueError: Could not find guild with that id.
    :raises Other: Raised in the obj.add_message() method


remove_object
========================
.. autofunction:: daf.core.remove_object

