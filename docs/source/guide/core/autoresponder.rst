======================
Automatic responder
======================

.. versionadded:: 4.0.0

Discord Advertisement Framework also supports the so called automatic responder.

The automated responder can promptly reply to messages directed to either the guild or private messages.
It can be customized to trigger based on specific keyword patterns within a message,
provided the constrains are met.

.. warning::

  For the automatic responder to work, :class:`~daf.client.ACCOUNT`'s ``intents`` parameter
  needs to have the following intents enabled:

  - members
  - guild_messages
  - dm_messages
  - message_content

  .. code-block:: python

    intents = Intents.default()
    intents.members=True
    intents.guild_messages=True
    intents.dm_messages=True
    intents.message_content=True


There are 2 responder classes:

- :class:`daf.responder.DMResponder` - responds to messages sent into the bot's direct messages.
- :class:`daf.responder.GuildResponder` - responds to messages sent into a guild channel.
  The bot must be joined into that guild, otherwise it will not see the message.


They can be used on each account through the :class:`~daf.client.ACCOUNT`'s ``responders`` parameter.
The parameter is a list of responders.

.. code-block:: python
  :linenos:

  import daf
  
  daf.client.ACCOUNT(
    ...,
    responders=[daf.responder.DMResponder(...), ...]
  )


Both responders accept the following parameters:

:condition:

  Represents the message match condition.
  If both the condition and the constraints are met, then an action (response)
  will be triggered.

  The :ref:`Matching logic` chapter explains how matching is done (same as :class:`daf.guild.AutoGUILD`
  and :class:`daf.message.AutoCHANNEL`)

:action:

  Represent the action taken upon message match (and constraint fulfillment).
  Currently the only action is a message response.
  There are 2 types of responses, which both send a message in response to the original trigger message.

  .. grid:: 2

    .. grid-item-card:: :class:`~daf.responder.actions.response.DMResponse`

      Will send a reply to the message author's private messages.

    .. grid-item-card:: :class:`~daf.responder.actions.response.GuildResponse`

      Will send a reply to same channel as the trigger message.

      This is only available for the :class:`~daf.responder.GuildResponder` responder.

  Both response classes accept a single parameter ``data`` of base type
  :class:`~daf.messagedata.BaseTextData`, which represents the data that will be sent in the response message.
  The :class:`~daf.messagedata.BaseTextData` type has two different implementations:

  - :class:`~daf.messagedata.TextMessageData` - for fixed data

    .. code-block:: python

      import daf

      daf.responder.DMResponse(
          data=daf.messagedata.TextMessageData("My content")
      )
      
  - :class:`~daf.messagedata.DynamicMessageData` - for data obtained through a function.

    .. code-block:: python

        import daf
        import requests

        class MyCustomText(DynamicMessageData):
            def __init__(self, a: int):
                self.a = a

            def get_data(self):  # Can also be async
                mydata = requests.get('https://daf.davidhozic.com').text
                return TextMessageData(content=mydata)

        daf.responder.DMResponse(
            data=MyCustomText(5)
        )

:constraints:

  In addition to the ``condition`` parameter, constrains represent extra checks.
  These checks (constraints) must all be fulfilled, otherwise no reply will me made to the trigger message.

  A constraint can be any class implementing a constraint interface. The constraint interface is different
  for different responder types:
  
  .. grid:: 2

    .. grid-item-card:: :class:`daf.responder.DMResponder`

      Constraints are implementations of the
      :class:`~daf.responder.constraints.dmconstraint.BaseDMConstraint` interface.

      Built-in implementations:

      - :class:`~daf.responder.constraints.dmconstraint.MemberOfGuildConstraint`


    .. grid-item-card:: :class:`daf.responder.GuildResponder`

      Constraints are implementations of the
      :class:`~daf.responder.constraints.guildconstraint.BaseGuildConstraint` interface.

      Built-in implementations:

      - :class:`~daf.responder.constraints.guildconstraint.GuildConstraint`
    


  In addition to the built-in implementations, custom constrains can be made
  by implementing one of the two interfaces.

  .. code-block:: python
    :caption: Custom constraint implementation

    from daf import discord
    from daf.responder import GuildResponder
    from daf.responder.constraints import BaseGuildConstraint

    class MyConstraint(BaseGuildConstraint):
        def __init__(self, <some parameters>): ...

        def check(self, message: discord.Message, client: discord.Client) -> bool:
          return <True / False>
      
    GuildResponder(..., constraints=[MyConstraint(...)])
  


Here is a full example of a DM responder:

.. image:: ./DEP/Examples/AutoResponder/auto_dm_responder_example.png
  :width: 20cm


.. literalinclude:: ./DEP/Examples/AutoResponder/auto_dm_responder.py
  :language: python
  :linenos:


In the above example, we can see that the :class:`daf.responder.DMResponder` has a :class:`~daf.responder.logic.regex`
condition defined. The RegEx pattern is as follows: ``(buy|sell).*nft``.
We can interpret the pattern as "match the message when it contains either the word "buy" or "sell", followed by any text
as long as "nft" also appears (after "buy" / "sell" ) in that text.
We can also see a :class:`~daf.responder.constraints.dmconstraint.MemberOfGuildConstraint` instance.
It is given a ``guild=863071397207212052`` ID parameter, which only allows a response
if the author of the DM message is a member of the guild (server) with ID 863071397207212052.

The ``intents`` parameter of our :class:`~daf.client.ACCOUNT` defines 4 intents.
Intents are settings of which events Discord will send to our client.
Without them the auto responder does not work.
