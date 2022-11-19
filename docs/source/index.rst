=========================================================
DAF (|version|)
=========================================================
The Discord advertisement framework is a  **shilling tool** that allows easy advertising on Discord.

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
- Ability to run on **user** accounts or **bot** accounts

.. caution::
    While running this on user accounts is possible, it is :strong:`not recommended` since it is against Discord's ToS.
    I am not responsible if your account get's disabled for using self-bots!

- Periodic advertisement to **Direct (Private) Messages**, **Text channels** and **Voice channels**
- Advertising with either static data (text, embed, files, audio) or **dynamic data** (the data is obtained thru a function dynamically)
- Logging of sent messages to different outputs (also includes SQL)
- Ability to add additional application layers with help of asyncio
- Easy to setup

----------------------
Installation
----------------------
DAF can be installed though command prompt/terminal using the bottom commands.

.. tab-set::

    .. tab-item:: Main package
        
        Pre-requirement: `Python (minimum v3.8) <https://www.python.org/downloads/>`_

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
    ref
    changelog
