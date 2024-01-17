======================
Automatic responder
======================

.. versionadded:: 3.3.0

Discord Advertisement Framework also supports the so called automatic responder.

The automated responder can promptly reply to messages directed to either the guild or private messages.
It can be customized to trigger based on specific keyword patterns within a message,
provided the constrains are met.


There are 2 responder classes:

- :class:`daf.responder.DMResponder` - responds to messages sent into the bot's direct messages.
- :class:`daf.responder.GuildResponder` - responds to messages sent into a guild channel.
  The bot must be joined into that guild, otherwise it will not see the message.

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

      This can be used for matching text messages containing a certain sub-text or a word.
      As a parameter it accepts the sub-text used for checking.
      Usually, :class:`~daf.responder.logic.contains` would be used alongside logical operations,
      such as :class:`~daf.responder.logic.or_`, to match any of the multiple words (sub-texts).

  .. dropdown:: Logical operations
    :icon: diff-added
    :animate: fade-in-slide-down

    Logical operations are used to combine multiple text matching operations, as well as other
    nested logical operations. They themselves, do not match the text inside a message.
    They accept a list of operants (logical operations / matching operations).

    .. dropdown:: :class:`~daf.responder.logic.and_`
      :animate: fade-in-slide-down
      :icon: x

      Represents a logical AND operation.
      :class:`~daf.responder.logic.and_` evaluates to true when all of the operants inside are evaluate to true.
      
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


    .. dropdown:: :class:`~daf.responder.logic.not_`
      :animate: fade-in-slide-down
      :icon: horizontal-rule



:action:
:constraints:


