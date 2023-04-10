=========================================================
DAF (|version|)
=========================================================
The Discord advertisement framework is a Python based **shilling framework** that allows easy advertising on Discord.

**Documentation** can be found `here <https://daf.davidhozic.com>`_.


.. figure:: ./docs/images/daf-gui-front.png
    :width: 15cm

    Graphical interface (GUI)

.. figure:: ./docs/images/daf-console-run.png
    :width: 15cm

    Script (for running in console)


----------------------
Key features
----------------------
- Graphical Interface (GUI) / Console (script)
- Multi-account support
- Periodic and scheduled advertisements,
- Logging and analytics of sent messages (including SQL) - :ref:`Logging (core)`
- Easy to setup
- Asynchronous

.. caution::
    While running this on user accounts is possible, it is against Discord's ToS.
    I am not responsible if your account get's disabled for using self-bots!

----------------------
Installation
----------------------
DAF can be installed though command prompt/terminal using the bottom commands.

Pre-requirement: `Python (minimum v3.10) <https://www.python.org/downloads/>`_.

**Main package**

.. code-block:: bash

    pip install discord-advert-framework

**Voice**
            
.. code-block:: bash
    :caption: Voice Messaging / AUDIO

    pip install discord-advert-framework[voice]


.. code-block:: bash
    :caption: Proxy support

    pip install discord-advert-framework[proxy]

**SQL**
            
.. code-block:: bash
    :caption: SQL logging

    pip install discord-advert-framework[sql]


            
Install all of the (left) optional dependencies

.. code-block:: bash
    :caption: All

    pip install discord-advert-framework[all]
