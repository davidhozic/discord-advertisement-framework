=========================================================
Discord Advertisement Framework (|version|)
=========================================================
The Discord advertisement framework is a Python based automatic application that allows **easy automatic advertisement** (and much more) on Discord.

.. image:: ./DEP/daf-gui-front.png


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


------------------
Need help?
------------------

- Checkout the guides:

  - :ref:`Guide (GUI)` 
  - :ref:`Guide (core)`

- Contact me in my `Discord server <https://discord.gg/DEnvahb2Sw>`_.

----------------------
Key features
----------------------
- Automatic periodic and scheduled messages to multiple servers and channels,
- Error checking and recovery,
- Message logging, invite link tracking & statistics
- Multi-account support
- Graphical Interface (GUI) / Console (script)
- Easy to setup
- Programmatic usage
- Much more


.. note::
    Running on user accounts is against Discord ToS, however DAF still enables it.

----------------------
Installation
----------------------
DAF can be installed though command prompt/terminal using the bottom commands.

.. tab-set::

    .. tab-item:: Main package
        
        Pre-requirement: `Python (minimum v3.9) <https://www.python.org/downloads/>`_

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

            .. tab-item:: SQL
                
                - .. code-block:: bash
                    :caption: SQL logging

                    pip install discord-advert-framework[sql]

            .. tab-item:: Chrome integration

                - .. code-block:: bash
                     :caption: Chrome integration
                     
                     pip install discord-advert-framework[web]

            .. tab-item:: All
                
                Install all of the (left) optional dependencies

                - .. code-block:: bash
                    :caption: All

                    pip install discord-advert-framework[all]


----------------------
Table of contents
----------------------
.. toctree::
    :maxdepth: 2

    guide/index
    reference/index
    changelog
