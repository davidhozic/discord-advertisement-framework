=========================================================
DAF (|version|)
=========================================================
The Discord advertisement framework is a tool that allows easy advertising on Discord.

.. warning::
        **Version v1.9.5 is not yet released** or even ready. The **lastest version is v1.9**.

        Anything that has a **"Changed in v1.9.5"** or **"Added in v1.9.5"** is **not yet available**!


Links
----------------------
.. tab:: Index

    .. toctree::
        :maxdepth: 1

        getting_started
        ref
        logging
        changelog

.. tab:: My links

    - `Github <https://github.com/davidhozic/discord-advertisement-framework>`_
    - `Releases <https://github.com/davidhozic/discord-advertisement-framework/releases>`_
    - `Examples <https://github.com/davidhozic/discord-advertisement-framework/tree/master/Examples>`_


.. tab:: PyCord

    This framework uses a Discord API wrapper called PyCord and it is built to allow working directly with Pycord (eg. framework objects accept Pycord objects as arguments).

    Links:
    
    - `PyCord GitHub <https://github.com/Pycord-Development/pycord>`_
    - `PyCord Documentation <https://docs.pycord.dev/en/master/>`_



Key features
-------------------
- Periodic advertisement to **Direct (Private) Messages**, **Text channels** and **Voice channels**
- Advertising with either static data (text, embed, files, audio) or **dynamic data** (the data is obtained thru a function dynamically)
- Logging of send attempts with **JSON** file logs or to a **SQL** server (Microsoft SQL Server only).
- Ability to add additional application layers with help of asyncio
- Easy to setup
- Ability to run on **user** accounts or **bot** accounts

.. warning::
    While running this on user accounts is possible, it is not recommended since it is against Discord's ToS.


Installation
-------------------
To install the framework use one of the following:

.. code-block:: bash

    # Windows
    python -m pip install discord-advert-framework

.. code-block:: bash

    # Windows
    py -3 -m pip install discord-advert-framework

.. code-block:: bash
    
    # Linux
    python3 -m pip install discord-advert-framework




