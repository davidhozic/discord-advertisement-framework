=========================================================
DAF
=========================================================
.. image:: docs/source/images/logo.png
    :width: 100
    
The Discord advertisement framework is a  **shilling tool** that allows easy advertising on Discord.

----------------------
Other information
----------------------
For more information see the project's `Webpage <https://daf.davidhozic.com>`_.

----------------------
Key features
----------------------
- Ability to run on **multiple** accounts at once, either as a **self-bot** (personal account) or a **normal bot** account.

.. caution::
    While running this on user accounts is possible, it is :strong:`not recommended` since it is against Discord's ToS.
    I am not responsible if your account get's disabled for using self-bots!

- Periodic advertisement to **Direct (Private) Messages**, **Text channels** and **Voice channels**
- **Automatic guild/channel discovery**
- Dynamically obtained shill data
- Error recovery
- Logging of sent messages (including SQL)
- Async framework
- Easy to setup, with minimal code

--------------------
Basic example
--------------------
For basic example see `main_send_multiple.py <https://github.com/davidhozic/discord-advertisement-framework/blob/master/Examples/Message%20Types/TextMESSAGE/main_send_multiple.py>`_
