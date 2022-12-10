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
.. function:: daf.core.add_object(obj: client.ACCOUNT) -> None
    
    Adds an account to the framework.
    
    :Parameters:
        - obj: client.ACCOUNT
              The account object to add
    
    :Raises:
        - ValueError
              The account has already been added to the list.
        - TypeError
              ``obj`` is of invalid type.


add_object
========================
.. function:: daf.core.add_object(obj: guild.USER | guild.GUILD | guild.AutoGUILD,snowflake: client.ACCOUNT) -> None
    
    Adds a guild or an user to the daf.
    
    :Parameters:
        - obj: guild.USER | guild.GUILD | guild.AutoGUILD
              The guild object to add into the account (``snowflake``).
        - snowflake: client.ACCOUNT=None
              The account to add this guild/user to.
    
    :Raises:
        - ValueError
              The guild/user is already added to the daf.
        - TypeError
              The object provided is not supported for addition.
        - TypeError
              Invalid parameter type.
        - RuntimeError
              When using deprecated method of adding items to the shill list,
        no accounts were available.
        - Other
              Raised in the obj.initialize() method


add_object
========================
.. function:: daf.core.add_object(obj: message.DirectMESSAGE | message.TextMESSAGE | message.VoiceMESSAGE,snowflake: int | guild.GUILD | guild.USER) -> None
    
    Adds a message to the daf.
    
    :Parameters:
        - obj: message.DirectMESSAGE | message.TextMESSAGE | message.VoiceMESSAGE
              The message object to add into the daf.
        - snowflake: int | guild.GUILD | guild.USER | discord.Guild | discord.User | discord.Object
              Which guild/user to add it to (can be snowflake id or a framework _BaseGUILD object or a discord API wrapper object).
    
    :Raises:
        - TypeError
              The object provided is not supported for addition.
        - ValueError
              guild_id wasn't provided when adding a message object (to which guild should it add)
        - ValueError
              Missing snowflake parameter.
        - ValueError
              Could not find guild with that id.
        - Other
              Raised in the obj.add_message() method


remove_object
========================
.. autofunction:: daf.core.remove_object

