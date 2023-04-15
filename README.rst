=========================================================
Discord Advertisement Framework (Shiller)
=========================================================
The Discord advertisement framework is a Python based **shilling framework** that allows easy advertising on Discord.

**Documentation** can be found `here <https://daf.davidhozic.com>`_.


.. image:: ./docs/images/daf-gui-front.png
    :width: 15cm

.. image:: ./docs/images/daf-console-run.png
    :width: 15cm


----------------------
Key features
----------------------
- Graphical Interface (GUI) / Console (script)
- Multi-account support
- Periodic and scheduled advertisements,
- Logging and analytics of sent messages (including SQL)
- Easy to setup
- Asynchronous

.. caution::
    While running this on user accounts is possible, it is against Discord's ToS.
    I am not responsible if your account get's disabled for using self-bots!

----------------------
Installation
----------------------
DAF can be installed though command prompt/terminal using the bottom commands.

Pre-requirement: `Python (minimum v3.8) <https://www.python.org/downloads/>`_.

**Main package**

::

    pip install discord-advert-framework

**Voice Messaging / AUDIO**

::

    pip install discord-advert-framework[voice]

**Proxies**

::

    pip install discord-advert-framework[proxy]

**SQL logging**
            
::

    pip install discord-advert-framework[sql]


            
**All of the above (full package)**

::

    pip install discord-advert-framework[all]
