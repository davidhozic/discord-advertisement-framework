
=========================
Framework control (core)
=========================
The following section shows how DAF's core can be started / stopped.
The first thing you need is the library installed, see :ref:`Installation`.

The framework can be started using :func:`daf.core.run` function and stopped with the :func:`daf.core.shutdown` function.
It can also be stopped by a SIGINT signal, which can be signaled using CTRL+C.
For full list of parameters refer to :func:`daf.core.run`'s description.

.. code-block:: python

    import daf
    daf.run()

The above code is somewhat useless as nothing was configured.
:ref:`On the next page <Shilling list definition (core)>`,
we will take a look on how to define our accounts, guilds (servers) and messages.
