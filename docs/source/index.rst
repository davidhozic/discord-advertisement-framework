=========================================================
DAF (|version|)
=========================================================
The Discord advertisement framework is a Python based **shilling framework** that allows easy advertising on Discord.

---------------------
Links
---------------------
.. tab-set::
    
    .. tab-item:: Project

        - `Github <https://github.com/davidhozic/discord-advertisement-framework>`_
        - `Examples <https://github.com/davidhozic/discord-advertisement-framework/tree/master/Examples>`_
        - `Releases <https://github.com/davidhozic/discord-advertisement-framework/releases>`_

    .. tab-item:: API Wrapper (Pycord)

        This framework uses a Discord API wrapper called PyCord and it is built to allow working directly with Pycord (eg. framework objects accept Pycord objects as arguments).

        - `PyCord GitHub <https://github.com/Pycord-Development/pycord>`_
        - `PyCord Documentation <https://docs.pycord.dev/en/master/>`_


----------------------
Key features
----------------------
- Ability to run on **multiple** accounts at once, either on a personal account or as **normal bot** account.

.. caution::
    While running this on user accounts is possible, it is :strong:`not recommended` since it is against Discord's ToS.
    I am not responsible if your account get's disabled for using self-bots!

- Periodic advertisement to different channels,
- Login with username/password - :ref:`Automatic login`,
- Automatic guild discovery and join - :ref:`Automatic guild discovery and join`,
- Logging of sent messages (including SQL) - :ref:`Logging`
- Async framework
- Easy to setup, with minimal code

----------------------
Installation
----------------------
DAF can be installed though command prompt/terminal using the bottom commands.

.. tab-set::

    .. tab-item:: Main package
        
        Pre-requirement: `Python (minimum v3.10) <https://www.python.org/downloads/>`_

        .. code-block:: bash

            pip install discord-advert-framework

    .. tab-item:: Additional functionality
        
        Some functionality needs to be installed separately.
        This was done to reduce the needed space by the daf.
        
        .. tab-set::
        
            .. tab-item:: Voice
                
                - .. code-block:: bash
                    :caption: Voice Messaging / AUDIO

                    pip install discord-advert-framework[voice]

            .. tab-item:: Proxies

                - .. code-block:: bash
                    :caption: Proxy support

                    pip install discord-advert-framework[proxy]

            .. tab-item:: SQL
                
                - .. code-block:: bash
                    :caption: SQL logging

                    pip install discord-advert-framework[sql]

            .. tab-item:: All
                
                Install all of the (left) optional dependencies

                - .. code-block:: bash
                    :caption: SQL logging

                    pip install discord-advert-framework[all]





----------------------
Table of contents
----------------------
.. toctree::
    :maxdepth: 2

    guide/index
    reference/index
    changelog
