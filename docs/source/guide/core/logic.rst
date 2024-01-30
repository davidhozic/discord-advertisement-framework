======================
Matching logic
======================
Before going into the automatic guild definition and automatic channel definition,
we first need to explain how their patterns are matched.
Automatic guild definition, automatic channel definition and also :ref:`Automatic responder` determine
the match by considering a logic pattern.
The logic pattern can either be an actual logical operations (and, or, not) or a text-matching operation.


.. dropdown:: Text matching operations
    :icon: comment-discussion
    :animate: fade-in-slide-down

    These operations are used for matching actual text.
    Two types currently exist. They are the RegEx type, for matching based on a regex pattern, and a contains
    type, for matching when the text input contains the (single) configured keyword.

    .. caution::

        Text matching is **lower-case**. This means that all the message content
        will be interpreted as lower-case characters.
        
        When writing patterns, make sure the pattern words are lower-case.

    .. dropdown:: :class:`~daf.logic.regex`
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
        
            RegEx is sensitive to spaces around the ``|`` (the logical OR) character.
            When a space is inserted into a RegEx pattern, it is considered as something that needs to appear
            for the text to be matched.

            For example, pattern ``hello | world`` would match if the text contains the
            "hello " sequence or the " world" sequence (notice the spaces).
            
            Thus, unless you want spaces to be matched as well, write ``buy.*nft|sell.*nft``
            instead of ``buy.*nft | sell.*nft``! This is especially important for server (guild) names.

        For testing RegEx patterns, the following site is recommended: https://regex101.com/.


    .. dropdown:: :class:`~daf.logic.contains`
        :animate: fade-in-slide-down

        This can be used for matching text messages containing a certain a word.
        As a parameter it accepts the word (``keyword``) used for checking.
        Usually, :class:`~daf.logic.contains` would be used alongside logical operations,
        such as :class:`~daf.logic.or_`, to match any of the multiple words.

.. dropdown:: Logical operations
    :icon: diff-added
    :animate: fade-in-slide-down

    Logical operations are used to combine multiple text matching operations, as well as other
    nested logical operations. Themselves, they do not match the text inside a message.

    .. dropdown:: :class:`~daf.logic.and_`
        :animate: fade-in-slide-down
        :icon: x

        Represents a logical *AND* operation.
        :class:`~daf.logic.and_` evaluates to true when all of the operands inside evaluate to true.
        
        For example, if we write:

        .. code-block:: python
            :linenos:

            and_(contains('buy'), contains('nft'), contains('dragon'))

        then the text message will be matched only if it contains all of the words "buy", "nft" and "dragon"
        (in any order).
        The above example would in a human-readable form look like
        ``contains('buy') and contains('nft') and contains('dragon')``, where the ``contains('word')``
        evaluates to a human-readable form of ``if 'word' is in message``.

    .. dropdown:: :class:`~daf.logic.or_`
        :animate: fade-in-slide-down
        :icon: plus

        Represents a logical *OR* operation.
        :class:`~daf.logic.or_` evaluates to true when any of the operands inside evaluate to true.

        For example, if we write:

        .. code-block:: python
            :linenos:

            or_(contains('buy'), contains('nft'), contains('dragon'))

        then the text message will be matched only if it contains any of the words "buy", "nft" and "dragon"
        (in any order).
        The above example would in a human-readable form look like
        ``contains('buy') or contains('nft') or contains('dragon')``.


    .. dropdown:: :class:`~daf.logic.not_`
        :animate: fade-in-slide-down
        :icon: horizontal-rule

        Represents a logical *NOT* operation.
        :class:`~daf.logic.not_` accepts a single operand and evaluates to true when that operand is false.
        Basically, it negates the operand.

        For example, if we write:

        .. code-block:: python
            :linenos:

            and_(contains('buy'), not_(contains('dragon')))

        then the text message will be matched only if it contains the word "buy" but doesn't contain the word "dragon".
        The above example would in a human-readable form look like ``contains('buy') and not contains('dragon')``.
