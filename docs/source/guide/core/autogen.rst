============================
Automatic Generation (core)
============================
This documents describes mechanisms that can be used to automatically generate objects.

---------------------------
Shilling scheme generation
---------------------------
While the servers can be manually defined and configured, which can be time consuming if you have a lot of 
guilds to shill into, DAF also supports automatic definition of servers and channels.
Servers and channels can be automatically defined by creating some matching rules described in the
:ref:`Matching logic` chapter of this guide.



Automatic GUILD generation
==============================

.. seealso::
    This section only describes guilds that the user **is already joined in**.
    For information about **discovering NEW guilds and automatically joining them** see 
    :ref:`Automatic guild discovery and join`

.. |AUTOGUILD| replace:: :class:`~daf.guild.AutoGUILD`
.. |GUILD| replace:: :class:`~daf.guild.GUILD`
.. |AUTOCHANNEL| replace:: :class:`~daf.message.AutoCHANNEL`

For a automatically managed servers, use |AUTOGUILD| which internally generates |GUILD| instances.
Simply create a list of |AUTOGUILD| objects and then pass it to the ``servers`` parameter of
:class:`daf.client.ACCOUNT`.

.. WARNING::

    Messages that are added to |AUTOGUILD| should have |AUTOCHANNEL| for the ``channels`` parameters,
    otherwise you will be spammed with warnings and only one guild will be shilled.


.. literalinclude:: ./DEP/Examples/AutomaticGeneration/main_autoguild.py


Automatic channel generation
==============================
For a automatically managed channels, use |AUTOCHANNEL|.
It can be passed to xMESSAGE objects to the ``channels`` parameters.

.. literalinclude:: ./DEP/Examples/AutomaticGeneration/main_autochannel.py
    :caption: AutoCHANNEL example
