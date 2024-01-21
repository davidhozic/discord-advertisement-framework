======================
Automatic responder
======================

.. versionadded:: 3.3.0

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
  If both the condition and the constraints are met, then a action (response)
  will be triggered.

  | The condition can be any class that inherits the :class:`~daf.responder.logic.BaseLogic` class.
  | These classes are:

  .. dropdown:: Text matching
    :icon: comment-discussion
    :animate: fade-in-slide-down

    These classes are used to match the text of a message directly.

    .. caution::

      Text matching is **lower-case**. This means that all the message content
      will be interpreted as lower-case characters.
      
      When writing patterns, make sure the pattern words are lower-case.

    .. dropdown:: :class:`~daf.responder.logic.regex`
      :animate: fade-in-slide-down

      This can be used for matching a RegEx (regular expression pattern).
      It is probably the most desirable as it allows flexible pattern matching.
      For example, if we want the message to contain the words "buy" and "nft",
      we can write our pattern like this: ``buy.*nft``. The former pattern will match
      when the message contains both words - "buy" and "nft", and "nft" appears after "buy".
      The ``.*`` means match any character (``.``) zero or infinite times (``*``).

      Here are some example messages the ``buy.*nft`` pattern will match:

      - "Where can I buy the NFTs?"
      - "May I buy the dragon NFT from you?"
      - "I would really want to buy the bunny NFT."

      Additionally, RegEx supports the logical *OR* operation.
      This can be done by separating multiple RegEx patterns with the ``|`` character.
      For example, the ``buy.*nft|sell.*nft`` pattern will match the text message if any of the 2 patterns (separated
      by ``|``) matches.

      .. caution::
        
        Unlike with :class:`daf.guild.AutoGUILD`, where the RegEx pattern allows spaces around the ``|``
        character, :class:`~daf.responder.logic.regex` does not.
        Guild names can't contain whitespace characters in the edges of the name, thus for simplicity reasons,
        spaces in the pattern get stripped. With :class:`daf.responder.logic.regex` they **do NOT** get stripped,
        so make sure you are writing ``buy.*nft|sell.*nft`` instead of ``buy.*nft | sell.*nft``!

      For testing RegEx patterns, the following site is recommended: https://regex101.com/.


    .. dropdown:: :class:`~daf.responder.logic.contains`
      :animate: fade-in-slide-down

      This can be used for matching text messages containing a certain a word.
      As a parameter it accepts the word (``keyword``) used for checking.
      Usually, :class:`~daf.responder.logic.contains` would be used alongside logical operations,
      such as :class:`~daf.responder.logic.or_`, to match any of the multiple words.

  .. dropdown:: Logical operations
    :icon: diff-added
    :animate: fade-in-slide-down

    Logical operations are used to combine multiple text matching operations, as well as other
    nested logical operations. Themselves, they do not match the text inside a message.

    .. dropdown:: :class:`~daf.responder.logic.and_`
      :animate: fade-in-slide-down
      :icon: x

      Represents a logical *AND* operation.
      :class:`~daf.responder.logic.and_` evaluates to true when all of the operands inside evaluate to true.
      
      For example, if we write:

      .. code-block:: python
        :linenos:

        and_(contains('buy'), contains('nft'), contains('dragon'))

      then the text message will be matched only if it contains all of the words "buy", "nft" and "dragon"
      (in any order).
      The above example would in a human-readable form look like
      ``contains('buy') and contains('nft') and contains('dragon')``, where the ``contains('word')``
      evaluates to a human-readable form of ``if 'word' is in message``.

    .. dropdown:: :class:`~daf.responder.logic.or_`
      :animate: fade-in-slide-down
      :icon: plus

      Represents a logical *OR* operation.
      :class:`~daf.responder.logic.or_` evaluates to true when any of the operands inside evaluate to true.

      For example, if we write:

      .. code-block:: python
        :linenos:

        or_(contains('buy'), contains('nft'), contains('dragon'))

      then the text message will be matched only if it contains any of the words "buy", "nft" and "dragon"
      (in any order).
      The above example would in a human-readable form look like
      ``contains('buy') or contains('nft') or contains('dragon')``.


    .. dropdown:: :class:`~daf.responder.logic.not_`
      :animate: fade-in-slide-down
      :icon: horizontal-rule

      Represents a logical *NOT* operation.
      :class:`~daf.responder.logic.not_` accepts a single operand and evaluates to true when that operand is false.
      Basically, it negates the operand.

      For example, if we write:

      .. code-block:: python
        :linenos:

        and_(contains('buy'), not_(contains('dragon')))

      then the text message will be matched only if it contains the word "buy" but doesn't contain the word "dragon".
      The above example would in a human-readable form look like ``contains('buy') and not contains('dragon')``.

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
      
  - :class:`~daf.messagedata.DynamicTextMessageData` - for data obtained through a function.

    .. code-block:: python

      import daf
      import requests

      def get_data():
          mydata = requests.get('https://daf.davidhozic.com').text
          return daf.messagedata.TextMessageData(content=mydata)

      daf.responder.DMResponse(
          data=daf.messagedata.DynamicTextMessageData(get_data)
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
  by implementing one of the two interfaces. This can be done by implementing the correct interface.
  For example:

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

.. image:: ./DEP/auto_dm_responder_example.png
  :width: 20cm


.. literalinclude:: ./DEP/auto_dm_responder.py
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
