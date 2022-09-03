=========================================================
DAF (|version|)
=========================================================
The Discord advertisement framework is a  **shilling tool** that allows easy advertising on Discord.




----------------------
Links
----------------------
.. tab-set::

    .. tab-item:: Index

        .. toctree::
            :maxdepth: 1

            getting_started
            ref
            logging
            changelog


    .. tab-item:: My links

        - `Github <https://github.com/davidhozic/discord-advertisement-framework>`_
        - `Releases <https://github.com/davidhozic/discord-advertisement-framework/releases>`_
        - `Examples <https://github.com/davidhozic/discord-advertisement-framework/tree/master/Examples>`_


    .. tab-item:: PyCord

        This framework uses a Discord API wrapper called PyCord and it is built to allow working directly with Pycord (eg. framework objects accept Pycord objects as arguments).

        Links:
        
        - `PyCord GitHub <https://github.com/Pycord-Development/pycord>`_
        - `PyCord Documentation <https://docs.pycord.dev/en/master/>`_




----------------------
Key features
----------------------
- Ability to run on **user** accounts or **bot** accounts
- Periodic advertisement to **Direct (Private) Messages**, **Text channels** and **Voice channels**
- Advertising with either static data (text, embed, files, audio) or **dynamic data** (the data is obtained thru a function dynamically)
- Logging of send attempts with **JSON** file logs or to a **SQL** server (Microsoft SQL Server only)
- Ability to add additional application layers with help of asyncio
- Easy to setup

.. caution::
    While running this on user accounts is possible, it is :strong:`not recommended` since it is against Discord's ToS.
    I am not responsible if your account get's disabled for using self-bots, however there are some protections to make
    it harder for the API to detect a self-bot.


----------------------
Installation
----------------------
.. tab-set::

    .. tab-item:: Windows

        .. code-block:: bash

            python -m pip install discord-advert-framework

        .. code-block:: bash

            py -3 -m pip install discord-advert-framework

    .. tab-item:: Linux

        .. code-block:: bash
            
            python3 -m pip install discord-advert-framework

    .. tab-item:: Additional functionality

        Some functionality needs to be installed separately.
        
        This was done to reduce the needed space by the daf.

        - .. code-block:: bash
            :caption: Voice Messaging / AUDIO

            pip install discord-advert-framework[voice]

        - .. code-block:: bash
            :caption: Proxy support

            pip install discord-advert-framework[proxy]
        
        - .. code-block:: bash
            :caption: SQL logging

            pip install discord-advert-framework[sql]

