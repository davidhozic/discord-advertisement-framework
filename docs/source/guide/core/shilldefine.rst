===============================
Shilling list definition (core)
===============================
This document holds information regarding shilling with message objects.

.. |TextMESSAGE| replace:: :class:`~daf.message.TextMESSAGE`
.. |VoiceMESSAGE| replace:: :class:`~daf.message.VoiceMESSAGE`
.. |DirectMESSAGE| replace:: :class:`~daf.message.DirectMESSAGE`
.. |GUILD| replace:: :class:`~daf.guild.GUILD`
.. |USER| replace:: :class:`~daf.guild.USER`

We will now see how our shilling / advertisement list can be defined.

----------------------------------
Definition of accounts (core)
----------------------------------

Discord accounts / clients are inside DAF represented by the :class:`daf.client.ACCOUNT` class.
It accepts many parameters, out of which these are the most important:

- ``token``: A string (text) parameter. It is the token an account needs to login into Discord.
  Token can be obtained through the `developer portal <https://discordgsm.com/guide/how-to-get-a-discord-bot-token>`_
  for bot accounts and through a browser for
  `user accounts <https://www.androidauthority.com/get-discord-token-3149920/>`_.
- ``is_user``:  An optional ``True`` / ``False`` parameter. Discord has 2 types of clients - user accounts and  bots.
  Set this to True when the above ``token`` belongs to a user and not a bot.
- ``proxy``: An optional string (text) parameter. Represents a proxy URL used to access Discord.
- ``servers``: A list of servers. In DAF, servers are referred to as "guild", which was Discord's original
  name for a server. Elements inside this list can be any objects inherited from :class:`daf.guild.BaseGUILD` class.
  Three types of servers exist (are inherited from  :class:`daf.guild.BaseGUILD`):
  
  - :class:`daf.guild.GUILD`
    
    Represents an actual Discord server with channels and members.

  - :class:`daf.guild.USER`
    
    Represents a user and their direct messages.

    .. caution::

        Shilling to DM's is not recommended as there is no way to check if our client has permissions.
        There is a high risk of Discord automatically banning you if you attempt to shill messages to users,
        who can't receive them from you.

  - :class:`daf.guild.AutoGUILD`

    Represents multiple Discord servers with channels and members, whose
    names match a configured pattern. Strictly speaking, this isn't actually inherited from
    :class:`daf.guild.BaseGUILD`, but is rather a wrapper for multiple :class:`daf.guild.GUILD`.
    It can be used to quickly define the entire the entire server list,
    without manually creating each :class:`daf.guild.GUILD`.

    Refer to the :ref:`Automatic Generation (core)` section for more information.



Now let's see an example.

.. code-block:: python
    :linenos:

    from daf.client import ACCOUNT
    import daf

    accounts = [
        ACCOUNT(
            token="HHJSHDJKSHKDJASHKDASDHASJKDHAKSJDHSAJKHSDSAD",
            is_user=True,  # Above token is user account's token and not a bot token.
            servers=[]
        )
    ]

    daf.run(accounts=accounts)


As you can see from the above example, the definition of accounts is rather simple.
Notice we didn't define our servers. We will do that in the next section.

After running the example, the following output is displayed.
Ignore the ``intents`` warnings for now. These warnings are not even relevant for user accounts.
Intents are settings of what kind of events the :class:`~daf.client.ACCOUNT` should listen to and are controlled
with its ``intents`` parameter. User accounts have no notion of intents.

Notice the first line of the output. It tells us that the logs will be stored into a specific folder.
DAF supports message logging, meaning that a message log is created for each sent message.
A logger can be given to the :func:`daf.core.run`'s ``logger`` parameter.
For more information about logging see :ref:`Logging (core)`.

::

    [2024-01-21 13:24:22.887679] (NORMAL) | daf.logging.logger_file: LoggerJSON logs will be saved to C:\Users\david\daf\History (None)
    [2024-01-21 13:24:22.887679] (WARNING) | daf.client: Members intent is disabled, it is needed for automatic responders' constraints and invite link tracking. (None)
    [2024-01-21 13:24:22.887679] (WARNING) | daf.client: Message content intent is disabled, it is needed for automatic responders. (None)
    [2024-01-21 13:24:22.887679] (NORMAL) | daf.client: Logging in... (None)
    [2024-01-21 13:24:25.910163] (NORMAL) | daf.client: Logged in as Aproksimacka (None)
    [2024-01-21 13:24:25.910163] (NORMAL) | daf.core: Initialization complete. (None)



--------------------------------------
Definition of servers / guilds (core)
--------------------------------------
We will only cover the definition of :class:`daf.guild.GUILD` here.
We will not cover :class:`daf.guild.USER` separately as the definition process is exactly
the same.
We will also not cover :class:`daf.guild.AutoGUILD` here, as it is covered in :ref:`Automatic Generation (core)`.

Let's define our :class:`daf.guild.GUILD` object now. Its most important parameters are:

- ``snowflake``: An integer parameter. Represents a unique identifier, which identifies every Discord resource.
  Snowflake can be obtained by
  `enabling the developer mode <https://beebom.com/how-enable-disable-developer-mode-discord/>`_,
  right-clicking on the guild of interest, and then left-clicking on *Copy Server ID*.
- ``messages``: A list parameter of our message objects. Message objects represent the content that will be sent
  into specific channels, with a specific period. For our :class:`daf.guild.GUILD`, messages can be
  the following classes:

  - :class:`daf.message.TextMESSAGE`: Message type for sending textual data. Data includes files as well.
  - :class:`daf.message.VoiceMESSAGE`: Message type for sending audio data / playing audio to voice channels.


Let's expand our example from :ref:`Definition of accounts (core)`.

.. code-block:: python
  :linenos:
  :emphasize-lines: 2, 10-13
  
  from daf.client import ACCOUNT
  from daf.guild import GUILD
  import daf

  accounts = [
      ACCOUNT(
          token="HHJSHDJKSHKDJASHKDASDHASJKDHAKSJDHSAJKHSDSAD",
          is_user=False,  # Above token is user account's token and not a bot token.
          servers=[
              GUILD(
                  snowflake=863071397207212052,
                  messages=[]
              )
          ]
      )
  ]

  daf.run(accounts=accounts)


Now let's define our messages.

--------------------------------------
Definition of messages (core)
--------------------------------------
Three kinds of messages exist. Additional to :class:`daf.message.TextMESSAGE`
and :class:`daf.message.VoiceMESSAGE`, is the :class:`daf.message.DirectMESSAGE` message type.
This message type is used together with :class:`daf.guild.USER` for sending messages into DMs.
Unlike the previously mentioned message types, :class:`~daf.message.DirectMESSAGE` does not have
the ``channels`` parameter.

Now let's describe some parameters.
The most important parameters inside :class:`daf.message.TextMESSAGE` are:

- ``data``: A :class:`~daf.messagedata.TextMessageData` object or
  a :class:`~daf.messagedata.DynamicMessageData` (Dynamically obtained data) inherited object.
  It represents the data that will be sent into our text channels.

- ``channels``: A list of integers or a single :class:`~daf.message.AutoCHANNEL` object. The integers
  inside a list represents channel snowflake IDs. Obtaining the IDs is the same as for
  :ref:`guilds <Definition of servers / guilds (core)>`.
  See :ref:`Automatic Generation (core)` for information about :class:`~daf.message.AutoCHANNEL`.

- ``period``: It represents the time period at which messages will be periodically sent.
  It can be one of the following types:

  - :class:`~daf.message.messageperiod.FixedDurationPeriod`: A fixed time period.
  - :class:`~daf.message.messageperiod.RandomizedDurationPeriod`: A randomized (within a certain range) time period.
  - :class:`~daf.message.messageperiod.DaysOfWeekPeriod`: A period that sends at
    multiple specified days at a specific time.
  - :class:`~daf.message.messageperiod.DailyPeriod`: A period that sends every day at a specific time.

Now that we have an overview of the most important parameters, let's define our message.
We will define a message that sends fixed data into a single channel, with a fixed time (duration) period.

.. code-block:: python
  :linenos:
  :emphasize-lines: 1-3, 19-23

  from daf.message.messageperiod import FixedDurationPeriod
  from daf.messagedata import TextMessageData
  from daf.message import TextMESSAGE
  from daf.client import ACCOUNT
  from daf.guild import GUILD

  from datetime import timedelta

  import daf

  accounts = [
      ACCOUNT(
          token="HHJSHDJKSHKDJASHKDASDHASJKDHAKSJDHSAJKHSDSAD",
          is_user=False,  # Above token is user account's token and not a bot token.
          servers=[
              GUILD(
                  snowflake=863071397207212052,
                  messages=[
                      TextMESSAGE(
                          data=TextMessageData(content="Looking for NFT?"),
                          channels=[1159224699830677685],
                          period=FixedDurationPeriod(duration=timedelta(seconds=15))
                      )
                  ]
              )
          ]
      )
  ]

  daf.run(accounts=accounts)


.. image:: ./images/message_definition_example_output.png
  :width: 20cm


Similarly to text messages, voice messages can be defined with :class:`daf.message.VoiceMESSAGE`.
Definition is very similar to :class:`daf.message.TextMESSAGE`. The only thing that differs from the above
example is the ``data`` parameter. That parameter is with :class:`~daf.message.VoiceMESSAGE` of type
:class:`~daf.messagedata.VoiceMessageData` (Fixed data) or
:class:`~daf.messagedata.DynamicMessageData` (Dynamically obtained data).
Additionally, it contains a ``volume`` parameter.


--------------------------------------
Message advertisement examples
--------------------------------------

The following examples show a complete core script setup needed to advertise periodic messages.

.. dropdown:: TextMESSAGE

  .. literalinclude:: ./DEP/Examples/MessageTypes/TextMESSAGE/main_send_multiple.py
    :caption: TextMESSAGE full example
    :linenos:

.. dropdown:: VoiceMESSAGE

  .. literalinclude:: ./DEP/Examples/MessageTypes/VoiceMESSAGE/main_send.py
    :caption: VoiceMESSAGE full example
    :linenos:

.. dropdown:: DirectMESSAGE

  .. literalinclude:: ./DEP/Examples/MessageTypes/DirectMESSAGE/main_send_multiple.py
    :caption: DirectMESSAGE full example
    :linenos:

Next up, we will take a look how to setup and use :ref:`message logging <Logging (core)>`.
