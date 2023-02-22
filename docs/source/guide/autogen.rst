=======================
Automatic generation
=======================
This documents describes mechanisms that can be used to automatically generate objects.

---------------------------
Shilling scheme generation
---------------------------
While the framework supports to manually define a schema, which can be time consuming if you have a lot of 
guilds to shill into and harder to manage, the framework also supports automatic generation of the schema.

.. _regex: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Regular_Expressions

Using this method allows you to have a completely automatically managed system of finding guilds and channels that match 
a specific regex_ pattern. It automatically finds new guilds/channels at initialization and also during normal framework operation.
This is great because it means you don't have to do much but it gives very little control of into what to shill.


Automatic GUILD generation
==============================

.. seealso::
    This section only describes guilds that the user **is already joined in**.
    For information about **discovering NEW guilds and automatically joining them** see 
    :ref:`Automatic guild discovery and join`

.. |AUTOGUILD| replace:: :class:`~daf.guild.AutoGUILD`
.. |GUILD| replace:: :class:`~daf.guild.GUILD`
.. |AUTOCHANNEL| replace:: :class:`~daf.message.AutoCHANNEL`

For a auto-managed GUILD list, use |AUTOGUILD| which internally generates |GUILD| instances.
Simply create a list of |AUTOGUILD| objects and then pass it to the framework.
It can be passed to the framework exactly the same way as |GUILD|
(see :ref:`quickstart` (``accounts``) and :ref:`Dynamically adding objects`).

.. WARNING::

    Messages that are added to |AUTOGUILD| should have |AUTOCHANNEL| for the ``channels`` parameters,
    otherwise you will be spammed with warnings and only one guild will be shilled.


.. literalinclude:: ../DEP/Examples/Automatic Generation/autoguild.py


Automatic channel generation
==============================
For a auto-managed channel list use |AUTOCHANNEL| instances.
It can be passed to xMESSAGE objects into the ``channels`` parameters instead of a list.

.. literalinclude:: ../DEP/Examples/Automatic Generation/autochannel.py
    :caption: AutoCHANNEL example
