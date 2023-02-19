==================================
Web browser
==================================

.. warning:: 

    This can only be used if you are running the framework in a desktop
    environment. You cannot use it eg. on a Ubuntu server.


DAF includes optional functionality that allows automatic guild joins and login with username and password instead
of token.

To use the web functionality, users need to install the optional packages with:

.. code-block:: bash

    pip install discord-advert-framework[web]


The Chrome browser is also required to run the web functionality.


.. note::

    When running the web functionality, the ``proxy`` parameter passed to :class:`~daf.client.ACCOUNT`, will also
    be used to the browser.

    Unfortunetly it is not directly possible for the web driver to accept a proxy with username and password, meaning
    just the normal "protocol://ip:port" proxy will work. If you plan to run a private proxy, it is recommened that
    you whitelist your IP instead and pass the ``proxy`` paramterer in the "protocol://ip:port" format.


Automatic login
========================
To login with username (email) and password instead of the token, users need to provide the :class:`~daf.client.ACCOUNT`
object with the ``username`` and ``password`` parameters.

.. code-block:: python
    :emphasize-lines: 5, 6

    import daf

    accounts = [
        daf.ACCOUNT(
            username="myemail@gmail.com",
            password="TheRiverIsFlowingDownTheHill232",
            ...
        )
    ]

    
    daf.run(accounts=accounts)

If you run the above snippet, DAF will first open the browser, load the Discord login screen and login, then it will
save the token into a file under "daf_web_data" folder and send the token back to the framework. The framework will then
run exactly the same as it would if you passed it the token directly.

If you restart DAF, it will not re-login, but will just load the data from the saved storage under
"daf_web_data" folder.


Automatic guild discovery and join
======================================
The web layer beside login with username and password, also allows (semi) automatic guild discovery and join.

To use this feature, users need to create an :class:`~daf.guild.AutoGUILD` instance, where they pass the ``auto_join``
parameter. ``auto_join`` parameter is a :class:`~daf.web.GuildDISCOVERY` object, which can be configured how it should
search for new guilds.

.. warning::
    
    When joining a guild, users may be prompted to complete the **CAPTCHA** (Completely Automated Public Turing Check
    to tell Computers and Humans Apart), which is why this is **semi**-automatic.
    In the case of this event, the browser will wait 90 seconds for the user to complete the CAPTCHA,
    if they don't it will consider the join to be a failure.
    
    .. image:: ../DEP/images/captcha.png
        :width: 200


.. code-block:: python
    :emphasize-lines: 10, 11

    from daf import QuerySortBy, QueryMembers
    import daf

    accounts = [
        daf.ACCOUNT(
            username="myemail@gmail.com",
            password="TheRiverIsFlowingDownTheHill232",
            servers=[
                daf.AutoGUILD(
                    ".*",
                    auto_join=daf.GuildDISCOVERY("NFT art", daf.QuerySortBy.TOP, limit=5),
                    ...
                )
            ]
        )
    ]

    
    daf.run(accounts=accounts)


With the above example, :class:`~daf.guild.AutoGUILD`, will search for guilds that match the ``prompt`` parameter and
select the ones that match the other parameters. After finding a guild, it will then check
if the ``include_pattern`` parameter of :class:`~daf.guild.AutoGUILD` matches with the guild name and if it does,
it will then obtain the invite link and try to join the guild.

The browser will only try to join as many guilds as defined by the ``limit`` parameter of
:class:`~daf.web.GuildDISCOVERY`. Guilds that the user is already joined, also count as a successful join, meaning
that if the limit is eg. 5 and the users is joined into 3 of the found guilds, browser will only join 2 new guilds.


Web feature example
=====================
The following shows an example of both previously described features.

.. literalinclude:: ../DEP/Examples/Web/main_web.py
    :language: python
