=========================================================
DAF
=========================================================
.. image:: docs/source/images/logo.png
    :width: 100
    
The Discord advertisement framework is a  **shilling tool** that allows easy advertising on Discord.

----------------------
Other information
----------------------
For more information see the project's `Webpage <https://daf.davidhozic.top>`_.

----------------------
Key features
----------------------
- Ability to run on **user** accounts (against discord's ToS) or **bot** accounts
- Periodic advertisement to **Direct (Private) Messages**, **Text channels** and **Voice channels**
- Advertising with either static data (text, embed, files, audio) or **dynamic data** (the data is obtained thru a function dynamically)
- Logging of send attempts with **JSON** file logs or to a **SQL** server (Microsoft SQL Server only)
- Ability to add additional application layers with help of asyncio
- Easy to setup

.. caution::
    While running this on user accounts is possible, it is :strong:`not recommended` since it is against Discord's ToS.
    I am not responsible if your account get's disabled for using self-bots, however there are some protections to make
    it harder for the API to detect a self-bot.

--------------------
Basic example
--------------------
For basic example see `main_send_string.py <Examples/Message%20Types/TextMESSAGE/main_send_string.py>`_
