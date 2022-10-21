=========================
Dynamic modification
=========================
This document describes how the framework can be modified dynamically.


----------------------------
Modifying the shilling list
----------------------------
See :ref:`Shilling list modification` for more information about the functions mentioned below.

While the shilling list can be defined statically (pre-defined) by creating a list and using the ``server_list``
parameter in the :func:`~daf.core.run` function (see :ref:`Quickstart` and :func:`~daf.core.run` (or :func:`~daf.core.initialize`)),
the framework also allows the objects to be added or removed dynamically from the user's program after the framework has already been started and initialized.

Dynamically adding objects
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Objects can be dynamically added using the :func:`daf.core.add_object` coroutine function.
The function can be used to add the following object types:

.. grid:: 2

    .. grid-item-card::

        Guilds
        ^^^^^^^^^^^^

        :class:`daf.guild.GUILD`

        :class:`daf.guild.USER`

    .. grid-item-card::
        
        Messages
        ^^^^^^^^^^^^
        :class:`daf.message.TextMESSAGE`

        :class:`daf.message.VoiceMESSAGE`

        :class:`daf.message.DirectMESSAGE`
        

.. note::   
    Messages can also be added thru the :py:meth:`daf.guild.GUILD.add_message`
    / :py:meth:`daf.guild.USER.add_message` method.

    .. caution::
        The guild must already be added to the framework, otherwise this method will fail.

    .. code-block:: python
        :emphasize-lines: 4

        ...
        my_guild = daf.GUILD(guild.id, logging=True)
        await daf.add_object(my_guild)
        await my_guild.add_message(daf.TextMESSAGE(...))
        ...

.. literalinclude:: ../../../Examples/Dynamic Modification/main_add_object.py
    :language: python
    :emphasize-lines: 25-27, 38


Dynamically removing objects
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
As the framework supports dynamically adding new objects to the shilling list, it also supports dynamically removing those objects.
Objects can be removed with the :func:`daf.core.remove_object`.


.. literalinclude:: ../../../Examples/Dynamic Modification/main_remove_object.py
    :language: python
    :emphasize-lines: 8, 15