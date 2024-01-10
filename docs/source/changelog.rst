========================
Changelog
========================
.. |BREAK_CH| replace:: **[Breaking change]**

.. |POTENT_BREAK_CH| replace:: **[Potentially breaking change]**

.. |UNRELEASED| replace:: **[Not yet released]**

------------------------
Info
------------------------

.. seealso:: 
    `Releases <https://github.com/davidhozic/discord-advertisement-framework/releases>`_  

.. note:: 
    The library first started as a single file script that I didn't make versions of.
    When I decided to turn it into a library, I've set the version number based on the amount of commits I have made since the start.


Glossary
======================
.. glossary::

    |BREAK_CH|
        Means that the change will break functionality from previous version.

    |POTENT_BREAK_CH|
        The change could break functionality from previous versions but only if it
        was used in a certain way.

    |UNRELEASED|
        Documented changes are not yet available to use.

---------------------
Releases
---------------------

v3.2.0
===================
- GUI:

  - Moved library tkclasswiz to a separate library on PyPI and made it a requirement.
  - Object nicknaming (part of tkclasswiz)
  - Type nicknaming (part of tkclasswiz)
  - Fixed bug where the object edit window could not be closed after trying to edit a non-editable object.

- |BREAK_CH| Minimum Python version bumped to **Python 3.9**.



v3.1.2
===================
- Fixed SQL compatibility
- Fixed "TypeError: can't compare offset-naive and offset-aware datetimes" exception when
  a rate limit happened (or slow mode).
- Fixed selenium timer reset when no join attempt was triggered.


v3.1.1
===================
- Fixed guild and text channels not fully visible in property view of GUI.


v3.1.0
===================
- Compatible with Python 3.12
- GUI:
  
  - ViewOnly structured data will display only the data that is provided, meaning
    the GUI will not be constructed based on type annotations of an objects, but rather
    based on the data itself.
  - Better toast notification format and compatibility across multiple DPI screens.
  - Graphical object library split into a separate package.

- :class:`daf.logging.LoggerJSON`:
  - ``index`` field is now a unique snowflake-like ID (used for removing logs).
  - |BREAK_CH| Invite logs will now contain a "member" dictionary
  for each invite log.
  - Analytics are now supported.

- LoggerCSV:
  - Analytics are now supported.
  - ``index`` field added in order to allow removal of logs.

- |BREAK_CH| Removed long time deprecated package "framework", which was the original import.


v3.0.4
====================
- Fixed AutoGUILD not working if the ``messages`` parameter is None.
- Fixed ``verify_ssl`` being ignored on the WebSocket connection.


v3.0.3
====================
- Fixed "Loading from JSON template causes live object reference to be lost".

v3.0.2
====================
- Fixed AutoGUILD not sending messages (events emitted prematurely).
- Fixed TextMESSAGE and VoiceMESSAGE not being removed after n sends when using AutoCHANNEL.
- Added missing :py:attr:`daf.guild.AutoGUILD.removed_messages` property.

v3.0.1
====================
- Downgraded Selenium version from 4.13 to 4.12 since 4.13 does not support headless, which
  undetected-chrome-driver is trying to set.

v3.0.0
====================
- SQL analytics:
  
  - Counts now have better error reporting when an invalid value was passed.

- GUI:

  - Higher refresh rate due to threading redesign - instead of calling Tkinter's root.update inside an asyncio task,
    the root.mainroot is called directly, while the asyncio event loop is running inside another thread.
  - The GUI will not block the asyncio tasks (explained in previous bullet).
  - When saving a new object definition, if the type of a parameter is literal, the value will be pre-checked inside
    the GUI and an exception will be raised if a valid value is not given.
  - Properties that start with ``_`` will no longer be displayed when viewing live structured objects.
  - Toast notifications for :func:`~daf.logging.tracing.trace`.
  - Parameter validation for literals, enums and bool.
  - Copy / Paste globally for both drop-down menus and list menus.

- Core:

  - New events system and module :ref:`Event reference`  
  - Updated PyCord API wrapper to 2.5.0 RC5
  - New property :py:attr:`daf.client.ACCOUNT.removed_servers` for tracking removed servers.
  - New property :py:attr:`daf.guild.GUILD.removed_messages` :py:attr:`daf.guild.USER.removed_messages`
    for tracking removed messages.
  - New parameter ``removal_buffer_length`` to :class:`daf.client.ACCOUNT` for setting maximum amount of
    of servers to keep in the :py:attr:`daf.client.ACCOUNT.removed_servers` buffer.
  - New parameter ``removal_buffer_length`` to :class:`daf.guild.GUILD` and :class:`daf.guild.USER`
    for setting maximum amount of messages to keep in the :py:attr:`daf.guild.GUILD.removed_messages`
    / :py:attr:`daf.guild.USER.removed_messages` buffer.

  - Event loop based API - All API methods that get called now submit an event in the event loop, which causes
    the API call to happen asynchronously unless awaited with ``await`` keyword. This also makes DAF
    much more efficient.

  - Remote:

    - Persistent WebSocket connection for receiving events from the core server
      (eg. :func:`~daf.logging.tracing.trace()` events).


  - Removed ``remaining_before_removal`` property from all message classes.
  - Added ``remove_after`` property to :class:`~daf.guild.GUILD`, :class:`~daf.guild.USER`,
    :class:`~daf.message.TextMESSAGE`, :class:`~daf.message.VoiceMESSAGE` and :class:`~daf.message.DirectMESSAGE`.


v2.10.4
======================
- Fixed prematurely exiting when waiting for captcha to be completed by user.


v2.10.3
======================
- Fixed Chrome driver not working with newer Chrome versions (115+).
- Fetching invite links better bypass.
- Remove invalid presence
- Fixed ``remaining_before_removal`` properties
- Fixed SQL queries not working on direct messages.


v2.10.2
=======================
- Fixed *Unclosed client session* warning when removing an user account.
- Fixed documentation of :func:`daf.core.shutdown` - removed information about non existent parameters.
- Selenium better waiting avoidance
- Fixed ACCOUNT not being removed from the list if the update failed and the re-login after update failed.


v2.10.1
=======================
- Fixed files in DirectMESSAGE.
- Fixed file paths over remote not having the full patch when returned back.
- Fixed files not having full path in the logs.
- Added :py:attr:`daf.dtypes.FILE.fullpath` to support the previous fix.
- Fixed exception when adding messages inside AutoGUILD, when one of the cached guilds fails initialization.
- Fixed serialization for :class:`discord.VoiceChannel`, which included slowmode_delay,
  even though the attribute doesn't exist in the VoiceChannel.


v2.10
====================
- GUI:

  - GUI can now be started with ``python -m daf_gui``
  - Deprecation notices are now a button.
  - Certain fields are now masked with '*' when not editing the object.
  - Old data that is being updated will now be updated by index
  - View properties of trackable objects. This can be used to, eg. view the channels AutoCHANNEL found.
  - 'Load default' button when editing :class:`discord.Intents` object.
  - A warning is shown besides the method execution frame to let users know, the data is not preserved.
  - Fixed accounts not being deleted when using delete / backspace keys in live view.

- Accounts:
  
  - Intents:

    - Added warnings for missing intents.
    - Intents.members is by default now disabled.

- Messages:

  - |BREAK_CH| Removed deprecated feature - YouTube streaming, in favor of faster startups and installation time. 
  - New property: :py:attr:`~daf.message.TextMESSAGE.remaining_before_removal`,
    :py:attr:`~daf.message.VoiceMESSAGE.remaining_before_removal`,
    :py:attr:`~daf.message.DirectMESSAGE.remaining_before_removal`
  - New parameter: ``auto_publish`` to :class:`~daf.message.TextMESSAGE` for automatically publishing messages sent to
    announcement (news) channels.

  - :class:`~daf.message.TextMESSAGE` and :class:`~daf.message.VoiceMESSAGE`'s ``remove_after`` parameter:

    - If integer, it will now work independently for each channel and will only decrement on successful sends.
    - If :class:`~datetime.datetime` or :class:`~datetime.timedelta`, it will work the same as before.

  - Moderation timeout handling (messages resume one minute after moderation timeout expiry)
  - Message content:

    - Deprecated :class:`daf.dtypes.AUDIO`, replaced with :class:`daf.dtypes.FILE`.
    - :class:`daf.dtypes.FILE` now accepts binary data as well and will load the data from ``filename`` at creation
      if the ``data`` parameter is not given.

- Web browser (Selenium):

  - Time between each guild join is now 45 seconds.
  - Selenium can now be used though remote, however it is not recommended.
  - Querying for new guilds will not repeat once no more guilds are found.


v2.9.7
=================
- Fixed channels not being visible though GUI, when using SQL logging.


v2.9.6
=================
- Fixed crash if ``start_period`` is larger than ``end_period``.
- Fixed local update not showing errors if updating objects under AutoGUILD


v2.9.5
=================
- Fixed incorrect caching of the SQL logs, causing incorrect values to be returned back to the GUI.
- Fixed detection of browser automation on searching for new guilds to join.


v2.9.4
=================
- Fixed :class:`AutoGUILD` concurrent access. When updating AutoGUILD, the update method did not block
  causing exceptions.
- Chrome driver fixes regarding to proxies and timeouts.


v2.9.3
=================
- Fixed :class:`AutoGUILD` and :class:`AutoCHANNEL` regex patterns. Users can now seperate names with "name1 | name2",
  instead of "name1|name2". `#380 <https://github.com/davidhozic/discord-advertisement-framework/issues/380>`_

v2.9.2
=================
- Fixed viewing dictionaries inside the GUI
- Other bug fixes present in :ref:`v2.8.5`


v2.9.1
=================
- Security update for yt-dlp


v2.9
=================
- GUI:

  - Template backups for each structured objects.
  - Rearanging of list items inside GUI listboxes
  - Connection timeout to a remote core is now 10 minutes for large datasets.
  - Dictionary editing - GUI nows allows to edit / view dictionary types (JSON). This could eg. be used
    to view SQL log's content which is saved to the database into JSON format.
  - Deprecation notices when creating a new object.
  - When opening color chooser and datetime select, the window now opens next to the button instead of window.

- Deprecation:
  
  - Deprecated Youtube streaming in :class:`~daf.dtypes.AUDIO` in favor of faster loading times.
    (Scheduled for removal in v2.10)

- Logging:
  
  - SQL logs can now be deleted though the :py:meth:`~daf.logging.sql.LoggerSQL.delete_logs`.


- Web (browser) layer:

  - Time between guild joins increased to 25 seconds to prevent rate limits.
  - Searching for invite links will be ignored if the user is already joined into the belonging guild.


v2.8.5
=================
- Fixed "Object not added to DAF" when accessing broken accounts from remote


v2.8.4
=================
- Fixed web browser waiting time being too little when searching invite links
- Fixed web browser could not create directory (username had a new line after it, now it auto strips that)
- Fix GUI not allowing to define inherited classes (eg. logging manager's fallback that inherits LoggerBASE)
- Fix item not in list error upon saving if an item was written inside a GUI's dropdown menu directly and then edited.


v2.8.3
=================
- Fixed new guilds being added whenever :class:`daf.client.ACCOUNT`'s update method failed.
- Fixed error if passing ``None`` inside update method of account for the ``servers`` parameter.
- Removed unneded check in object serialization (for remote) which slightly increases performance.
- Fixed Enum values being converted to objects when viewing live items / importing schema from live view.


v2.8.2
=================
- Fixed auto installation of ttkboostrap not opening the main window at the end.


v2.8.1
=================
- Fixed bug ``timezone required argument 'offset' when trying to save TextMESSAGE`` #325
- Fixed bug ``AutoGUILD incorrect type hints`` #326


v2.8
=================

- Remote control though HTTP access:

  - The core can be started on a remote server and then connected to and controlled by the graphical interface.
  - The GUI now has a dropdown menu where users can select between a local connection client and a remote connection client.
    Local connection client won't use the HTTP API, but will start DAF locally and interact with it directly.

- GUI:
  
  - Method execution
  - Executing method status window.
  - When editing objects, the Y size will now be set to default size every time the frame changes.
  - When executing async blocking functions, a progress bar window will be shown to indicate something is happening.

- Logging:

  - :class:`daf.logging.LoggerJSON` will create a new file once the current one reaches 100 kilobytes.
  - Improved performance of :class:`daf.logging.LoggerJSON`.
  - Loggers will now trace their output path, so users can find the output logs more easily.

- State preservation

  - When using the state preservation (introduced in :ref:`v2.7`), accounts that fail to login will, from now on,
    not be removed from list to prevent data loss.



v2.7
================
- Preserve objects state on shutdown (accounts, guilds, ...,) [logger not preserved]:
  
  - :func:`daf.core.run` function's ``save_to_file`` parameter or *Preserve state on shutdown* checkbox inside 
    *Schema definition* tab of the GUI to configure.

- Analytics:
  
  - Invite link tracking
  - :class:`~daf.guild.GUILD`: ``invite_track`` parameter for tracking invite links

- File outputs:

  - Changed all paths' defaults to be stored under /<user-home-dir>/daf/ folder to prevent permission problems

- :class:`~daf.guild.AutoGUILD` ``interval`` default changed to ``timedelta(minutes=1)``
- xMESSAGE ``start_in`` now accepts :class:`datetime.datetime` - send at specific datetime.
- GUI:
  
  - Live object view for viewing and live updating objects.
  - Invite link analytics
  - :class:`~discord.Intents` can now also be defined from the GUI.
  - Fixed schema save for enums (enums are not JSON serializable)

- Lowered logging-in timeout to 15 seconds

- |BREAK_CH| Removed DEPRECATED parameters for :func:`daf.core.run` and :func:`daf.core.initialize`:
    
  - ``token``
  - ``server_list``
  - ``is_user``
  - ``server_log_output``
  - ``sql_manager``
  - ``intents``
  - ``proxy``

- |BREAK_CH| Removed DEPRECATED function ``client.get_client``. This is replaced with :func:`daf.core.get_accounts`,
  from which the Discord client can be obtained by :py:attr:`daf.client.ACCOUNT.client` for each account.

- |BREAK_CH| Parameter ``debug`` in function :func:`daf.core.run` / :func:`daf.core.initialize` no longer accepts :class:`bool`.
  This was deprecated in some older version and now removed.

- |BREAK_CH| Removed DEPRECATED functionality inside ``add_object`` that allowed guilds to be added without passing the account
  to ``snowflake`` parameter. Before it implicitly took the first account from the shill list. This has been
  deprecated since :ref:`v2.4`.

- |BREAK_CH| Removed DEPRECATED functionality inside ``add_object`` that allowed snowflake ID and Discord's objects
  to be passed as ``snowflake`` parameter.

- |BREAK_CH| Removed DEPRECATED function ``get_guild_user``, which has been deprecated since :ref:`v2.4`.

- |BREAK_CH| ``xMESSAGE`` types no longer accept :class:`bool` for parameter ``start_in``. This has been deprecated
  since :ref:`v2.1`.


v2.6.3
=============
- Restored support for Python v3.8

v2.6.1
========
- Fixed logger not being converted properly when exporting GUI data into a script.

v2.6.0
==========
- Graphical User Interface - **GUI** for controlling the framework,
  defining the schema (with backup and restore) and script generation!

.. image:: ./DEP/daf-gui-front.png
    :align: center
    :scale: 40%

- Logging:
  
  - Added ``author`` field to all logging managers (tells us which account sent the message).
  - SQL analysis


v2.5.1
==========
- Fixed failure without SQL

v2.5
==========
- |BREAK_CH| Removed ``EMBED`` object, use ``daf.discord.Embed`` instead.
- |BREAK_CH| Removed ``timing`` module since it only contained deprecated objects.
- |BREAK_CH| Minumum Python version has been bumbed to **Python v3.10**.
- WEB INTEGRATION:
  
  - Automatic login and (semi-automatic) guild join though :class:`daf.web.SeleniumCLIENT`.
  - Automatic server discovery though :class:`daf.web.GuildDISCOVERY`


v2.4.3
=========
- Fixed missing documentation members


v2.4.2 (v2.3.4)
=================
- Fixed channel verification bug:

  - Fixes bug where messages try to be sent into channels that have not passed verification (complete button)

v2.4
=============
- Multiple accounts support:
  
  - Added :class:`daf.client.ACCOUNT` for running multiple accounts at once. Proxies are strongly recommended!
  - Deprecated use of:
    
    - token,
    - is_user,
    - proxy,
    - server_list,
    - intents
    
    inside the :func:`daf.core.run` function.

  - New function :func:`daf.core.get_accounts` that returns the list of all running accounts in the framework.

- Deprecated :func:`~daf.core.add_object` and :func:`~daf.core.remove_object` functions accepting API wrapper objects or ``int`` type for the ``snowflake`` parameter.
- Deprecated ``daf.core.get_guild_user`` function due to multiple accounts support.
- Deprecated ``daf.client.get_client`` function due to multiple accounts support.

v2.3
=============
- |BREAK_CH| Removed ``exceptions`` module, meaning that there are no DAFError derived exceptions from this version on.
  They are replaced with build-in Python exceptions.
- Automatic scheme generation and management:

  - :class:`daf.guild.AutoGUILD` class for auto-managed GUILD objects.
  - :class:`daf.message.AutoCHANNEL` class for auto-managed channels inside message.

- Debug levels:

  - Added deprecated to :class:`~daf.logging.tracing.TraceLEVELS`.
  - Changed the :func:`daf.core.run`'s debug parameter to accept a value from :class:`~daf.logging.tracing.TraceLEVELS`, to dictate
    what level trace should be displayed.

- :ref:`Messages` objects period automatically increases if it is less than slow-mode timeout.
- The :ref:`data_function`'s input function can now also be async.

v2.2
===========
- ``user_callback`` parameter for function :func:`daf.core.run` can now also be a regular function instead of just ``async``.
- Deprecated :class:`daf.dtypes.EMBED`, use :class:`discord.Embed` instead.
- |BREAK_CH| Removed ``get_sql_manager`` function.
- :func:`daf.core.run`:
    + Added ``logging`` parameter
    + Deprecated parameters ``server_log_output`` and ``sql_manager``.
- Logging manager objects: LoggerJSON, LoggerCSV, LoggerSQL
- New :func:`daf.logging.get_logger` function for retrieving the logger object used.
- :func:`daf.core.initialize` for manual control of asyncio (same as :func:`daf.core.run` except it is async)
- SQL:
    + SQL logging now supports **Microsoft SQL Server, MySQL, PostgreSQL and SQLite databases**.
    + |BREAK_CH| :class:`~daf.logging.sql.LoggerSQL`'s parameters are re-arranged, new parameters of which, the ``dialect`` (mssql, sqlite, mysql, postgresql) parameter must be passed.
- Development:
    + ``doc_category`` decorator for automatic documentation
    + Removed ``common`` module and moved constants to appropriate modules

v2.1.4
===========
Bug fixes:

- ``Fix incorrect parameter name in documentation``.

v2.1.3
===========
Bug fixes:

- ``[Bug]: KeyError: 'code' on rate limit #198``.

v2.1.2
===========
Bug fixes:

- #195 VoiceMESSAGE did not delete deleted channels.
- Exception on initialization of static server list in case any of the messages had failed their initialization.

v2.1.1
===========
- Fixed ``[Bug]: Predefined servers' errors are not suppressed #189``.
- Support for readthedocs.


v2.1
===========
- Changed the import ``import framework`` to ``import daf``. Using ``import framework`` is now deprecated.
- ``remove_after`` parameter:
    Classes: :class:`daf.guild.GUILD`, :class:`daf.guild.USER`, :class:`daf.message.TextMESSAGE`, :class:`daf.message.VoiceMESSAGE`, :class:`daf.message.DirectMESSAGE`

    now support the remove_after parameter which will remove the object from the shilling list when conditions met.
- Proxies:
    Added support for using proxies.
    To use a proxy pass the :func:`daf.run` function with a ``proxy`` parameter
- discord.EmbedField:
    |BREAK_CH| Replaced discord.EmbedField with discord.EmbedField.
- timedelta:
    start_period and end_period now support ``timedelta`` object to specify the send period.
    Use of ``int`` is deprecated

    |POTENT_BREAK_CH| Replaced ``start_now`` with ``start_in`` parameter, deprecated use of bool value.
- Channel checking:
    :class:`daf.TextMESSAGE` and :class:`daf.VoiceMESSAGE` now check if the given channels are actually inside the guild
- Optionals:
    |POTENT_BREAK_CH| Made some functionality optional: ``voice``, ``proxy`` and ``sql`` - to install use ``pip install discord-advert-framework[dependency here]``
- CLIENT:
    |BREAK_CH| Removed the CLIENT object, discord.Client is now used as the CLIENT class is no longer needed due to improved startup
- Bug fixes:
    Time slippage correction:
        This occurred if too many messages were ready at once, which resulted in discord's rate limit,
        causing a permanent slip.

        .. figure:: images/changelog_2_1_slippage_fix.png    

            Time slippage correction

    Slow mode correction:
        Whenever a channel was in slow mode, it was not properly handled. This is now fixed.


v2.0
===========
- New cool looking web documentation (the one you're reading now)
- Added volume parameter to :class:`daf.VoiceMESSAGE`
- Changed ``channel_ids`` to ``channels`` for :class:`daf.VoiceMESSAGE` and :class:`daf.TextMESSAGE`. It can now also accept discord.<Type>Channel objects.
- Changed ``user_id``/ ``guild_id`` to ``snowflake`` in :class:`daf.GUILD` and :class:`daf.USER`. This parameter now also accept discord.Guild (:class:`daf.GUILD`) and discord.User (:class:`daf.USER`)
- Added ``.update`` method to some objects for allowing dynamic modifications of initialization parameters.
- :class:`daf.AUDIO` now also accepts a YouTube link for streaming YouTube videos.
- New :ref:`Exceptions` system - most functions now raise exceptions instead of just returning bool to allow better detection of errors.
- Bug fixes and other small improvements.

v1.9.0
===========
- Added support for logging into a SQL database (MS SQL Server only). See :ref:`relational database log (SQL)`.
- :func:`daf.run` function now accepts discord.Intents.
- :func:`daf.add_object` and :func:`daf.remove_object` functions created to allow for dynamic modification of the shilling list.
- Other small improvements.

v1.8.1
===========
- JSON file logging.
- Automatic channel removal if channel get's deleted and message removal if all channels are removed.
- Improved debug messages.

v1.7.9
===========
- :class:`daf.DirectMESSAGE` and :class:`daf.USER` classes created for direct messaging.



