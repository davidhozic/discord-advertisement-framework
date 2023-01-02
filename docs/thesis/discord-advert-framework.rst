=====================================
Discord Advertisement Framework
=====================================

.. _Python: https://www.python.org

.. _DAFDOC: https://daf.davidhozic.com

.. |DAFDOC| replace:: DAF's documentation


.. note:: 
    
    The following document will refer to some objects that are found on external web documentation.
    Any links referencing functions/classes inside the project will open a page to |DAFDOC|_


.. figure:: ./DEP/images/logo.png
    :width: 3cm

    Discord Advertisement Framework logo
    (Made with DALL-E + Adobe Photoshop)


DAF Introduction
================================
Discord Advertisement Framework (from this point on, DAF) is a fully automatic shiller made part of the diploma.

It aims to eliminate the need of user presence while shilling is required.

I got the idea to make the project from a friend, who needed a way to automatically shill his NFT project, Ada Dragons.
The original project was just a simple script which was about 100 lines long, but since then the project has grown into a 
Python_ library consisting of ~5000 lines of original code.

The project's code is available on `Github <https://github.com/davidhozic/discord-advertisement-framework>`_.

The Python_ package is available on `PyPi (Python Package index) <https://pypi.org/project/Discord-Advert-Framework/>`_

The |DAFDOC|_ is available on https://daf.davidhozic.com .

It is important to mention that the framework itself is not a complete product, but rather half-product, which can
be quite quickly setup and thus turned into a full product with some very basic knowledge of the Python_ programming language.


Installation
================
DAF runs on Python_ so it is import that Python_ is installed on the machine.
DAF has been tested only on Windows and Linux, it is unknown how it works on Mac.

Once Python_ is installed, DAF can be installed with the following command:

.. code-block:: bash

    pip install discord-advert-framework


Basic usage
================
Once DAF is installed, users can create a Python_ script and start the framework with the :func:`daf.core.run` function which
accepts various parameters, the most important one being the ``accounts`` parameter which is a list of :class:`daf.client.ACCOUNT` instances.

The :class:`daf.client.ACCOUNT` accept different parameters the important ones being:

* token - The Discord's account authorization token
* is_user - Bool parameter that needs to be ``True`` if the ``token`` is from an user account.
* servers - A list of :class:`daf.guild.GUILD` / :class:`daf.guild.USER` that the user wants to shill too.

.. code-block::  python
    :caption: Example shilling script definition.
    :emphasize-lines: 6, 20

    from datetime import timedelta
    from daf import ACCOUNT, GUILD, USER, TextMESSAGE

    import daf

    accounts = [
        ACCOUNT(
            token="KSLKDJADNSJDBNAKDB", # Account token
            is_user=False,
            guilds=[
                GUILD(...), # First guild
                GUILD(...), # Second guild
                GUILD(...), # Third guild
                ...
            ]
        )
    ]

    # Start DAF
    daf.core.run(accounts=accounts)

The above :class:`daf.guild.GUILD` objects among others, accept 2 important parameters:

* snowflake - This is a universal identifier Discord uses on all their resources. Each resource has a unique ID.
* messages  - List of xMESSAGE instances which represent periodic messages that will be shilled into a server.

.. code-block:: python

    ...
    GUILD(
        snowflake=412098412094804,
        messages=[
            TextMESSAGE(...), # First message
            TextMESSAGE(...), # Second message
            TextMESSAGE(...), # Third message
            ...
        ]
    )
    ...

For sending direct messages to users :class:`daf.guild.USER` is used the same way.


The above :class:`daf.message.TextMESSAGE` objects accept the most parameters of all the classes available in DAF, but the only mandatory ones are:

* start_period - Accepts a :class:`datetime.timedelta` object which represents bottom range of a randomized shilling period. It can be None if fixed period is desired.
* end_period   - The same as start_period except it represents the upper range of the randomized period. If ``start_period`` is ``None``, the actual period is the same as end_period.
* data         - The data that is sent to Discord. It can in this case be:
    
  * :class:`str` - String (text) that is sent to the text channel.
  * :class:`discord.Embed` - API wrapper's object representing embedded messages. These are fancy formatted boxes with text, image, thumbnail, author, itd.
  * :class:`daf.dtypes.FILE` - Represents a file that is sent to Discord.
  * :class:`list` - List of any of the above types.
  * Special getter function for dynamically obtained (sent is what the function returns at individual call) data, see :func:`daf.dtypes.data_function` .

* channels - List of snowflakes which link to Discord channels where the shilling is required.


.. code-block:: python

    TextMESSAGE(
        start_period=timedelta(hours=2, minutes=30),
        end_period=timedelta(hours=4),
        data="Checkout my product!",
        channels=[314141234, 241421414124, 25152151512, 51251251512, ...]
    )


Once these has been defined the script is ready to use, simply run Python_ thru the console and pass the script file as the parameter.


The above shows how you can shill a constant textual content to a manually defined guild with manually defined text channels.
DAF also supports :class:`~daf.message.DirectMESSAGE`` for messaging users directly and :class:`~daf.message.VoiceMESSAGE`` for shilling audio content.

It also supports automatic guild definition based on regex and can join guilds automatically based on query parameter with :class:`~daf.guild.AutoGUILD` objects.
Channels can also be managed manually by using :class:`~daf.message.AutoCHANNEL` objects.
For more information about automatic shilling see :ref:`Automatic generation` .

Individual classes and function descriptions can be found on :ref:`Programming Reference` .

Additional guide is available on :ref:`Guide` .

