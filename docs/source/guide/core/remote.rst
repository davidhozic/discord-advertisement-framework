======================
Remote control (core)
======================

.. versionadded:: 2.8

While DAF can run completely standalone locally, it also allows to be run as a server that will accept connections from
a graphical interface (:ref:`Remote control (GUI)`).

The remote module spins up a HTTP server which can also be given a certificate and a private key allowing HTTPS connections.

To set up the core as a remote server, pass the :func:`~daf.core.run` function with the ``remote_client`` parameter.
It accepts an object of type :class:`daf.remote.RemoteAccessCLIENT`.

After the script is ran, DAF will listen and accept connections based on the configured options. While the server is running,
DAF can be used the same way as if there was no server at all.
