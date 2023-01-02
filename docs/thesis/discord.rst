===================
Discord
===================

.. _`Developer mode`: https://support.discord.com/hc/en-us/articles/206346498-Where-can-I-find-my-User-Server-Message-ID-

.. _`API Reference`: https://discord.com/developers/docs/topics/opcodes-and-status-codes

The project focuses on Discord shilling and in order to understand the rest of the thesis, 
this chapter contains some background information on Discord, including how it came to be and some basic information on how it works.


What is Discord
==================
Discord was created in 2015 by Discord Inc (formerly known as Hammer & Chisel), a game development studio founded by Jason Citron and Stanislav Vishnevskiy.
The platform was designed as a communication tool for gamers, specifically as a way for players to communicate with each other while playing games online.

The idea for Discord came from Citron's personal experience as a gamer.
He noticed that many of the existing communication tools (Skype, TeamSpeak) for gamers were outdated and difficult to use,
and he wanted to create a more user-friendly platform that would allow players to easily communicate with each other while playing games.

Discord has since evolved beyond just being a communication tool for gamers and has become a popular platform for communities of all kinds to come together and communicate.
It is now used by millions of users around the world for everything from gaming to education to socializing.

Discord is a popular communication platform that allows users to communicate through voice, video, and text chat. 
It is utilized by millions of people, primarily aged 13 and up, to connect with their communities and friends. 
Discord is often used for a variety of purposes, including discussing art projects, planning family trips, seeking homework assistance, and providing mental health support.
It also has a good search feature for searching content that was once posted which is useful for eg. finding the due date of a diploma that someone posted a month ago.

While Discord can be a home for communities of any size, it is particularly popular among smaller, active groups that frequently communicate with one another.
The majority of Discord servers are private and require an invitation to join, providing a space for friends and communities to stay connected.
However, there are also larger, more public communities centered around specific topics, such as popular video games like Minecraft and Fortnite 
or in the case of this thesis, things like blockchain and NFT.
It can also be used as a community of a school / faculty where students can talk via the voice channels, share study materials
and ask questions about the material they are confused about.
Some examples of Discord communities related to University of Ljubljana:

- :ref:`Student council of Faculty of Electrical Engineering (ŠSFE) <ssfe-community-fig>`,
- :ref:`FE UNI <fe-uni-community-fig>` ,
- FE VSŠ,
- FRI UNI,
- ...


Users have the ability to control their interactions on Discord and customize their experience on the platform.
They can choose who they interact with and what topics they engage in conversations about.
This personalization is one of the reasons why Discord is so beloved by its users.
It allows them to be themselves and connect with others who share similar interests and hobbies.


.. figure:: images/discord_logo.svg
    :width: 400

    Discord brand


.. _ssfe-community-fig:
.. figure:: images/ssfe_discord.png
    :width: 400

    ŠSFE Discord community


.. _fe-uni-community-fig:
.. figure:: images/feuni_discord.png
    :width: 400

    FE UNI Discord community


.. raw:: latex

    \newpage


Discord structure
==================

.. figure:: images/discord_client_struct.drawio.png

    Client structure

The Discord client is the application you can use to communicate.
At the core it consists of direct messages button, guilds (servers) list, channels list, and members list inside the guild.
There are 2 types of members the guild can have:

1. Users
2. Bots - Accounts used for automation.

It is against Discord's terms of services to automate user accounts.


Server roles
--------------
Discord has a role based permission system which means that each guild (server) has little things called
roles and each role controls what permission users with a certain role will have. 
Roles can be useful for hiding certain channels, especially if there are a lot of channels in the server.
For example you have a school community with channels for each different class, you can have roles for
1st year, 2nd year students, and give the "View channel" permission of a 2nd year classes only to 2nd year students.


Text channels
---------------
Text channels in Discord are indicated by the # symbol and are used for text-based communication.
To use a text channel, you can select it from the left-hand panel of the Discord client to view its content.
To send a message to a text channel, enter your message in the text box at the bottom of the client and press Enter.
In addition to text, you can also send GIFs, stickers, emojis, and gifts through the text box.
You can interact with previously-sent messages in the text channel by adding reactions, creating threads, and replying directly to messages, depending on your permissions or roles in the server.

.. figure:: images/discord_text_channel.png

    Discord text channel


Voice channels
---------------
Voice channels are channels on a Discord server that allow users to communicate with each other via voice.
Users can join and leave voice channels as they please, and can also mute and deafen themselves if they don't want to listen to or be heard by others.
Most Discord servers have a default voice channel called "AFK" (Away From Keyboard) where users who are inactive or need to step away from their computer are automatically moved. This helps to reduce clutter and noise in other voice channels.
Some servers also have voice channels with specific purposes, such as a voice channel for music, or one for gaming.
Voice channels can be password protected, or can be set to allow anyone to join.
In a voice channel, users can also use text chat to communicate with each other.
Voice channels can be used for many different purposes, such as casual conversation, gaming, music listening, or even professional meetings.

.. figure:: images/discord_voice_channel.png

    Discord voice channel


Direct messages
----------------
Discord's direct messages (DMs) are a convenient way to communicate privately with other users on the platform.
They allow users to send messages, share images and documents, and even voice and video call with one another and are very similar to :ref:`Text channels`.
DMs can be initiated by clicking on a user's profile or by mentioning them in a server.
They can be accessed from the main menu or from the user's contact list.
One of the great features of DMs is the ability to create group chats, allowing users to communicate with multiple people at once.
Discord also offers a "Do Not Disturb" mode, which allows users to silence their DMs while they are away or busy.
Overall, DMs are a valuable tool for connecting with friends and colleagues on Discord.



Snowflake ID
--------------
A Discord Snowflake is a unique ID assigned to every Discord user, channel, guild and other resources.
It is a 64-bit integer that is generated when the object is created and cannot be altered or reassigned.
The term "snowflake" refers to the unique and individual nature of the ID, similar to how no two snowflakes are exactly alike.

The Discord Snowflake ID system was implemented to solve the problem of assigning unique IDs to objects in a distributed system.
In the past, Discord had used timestamps to generate IDs, but this caused problems when multiple objects were created at the same time, resulting in non-unique IDs.
The Snowflake ID system avoids this problem by using a combination of a timestamp, a worker ID, and a sequence number to generate a unique ID.

One of the benefits of the Snowflake ID system is that it allows Discord to easily track the creation and deletion of objects.
The timestamp component of the ID allows Discord to determine when an object was created, and the sequence number allows them to determine the order in which objects were created.
This can be useful for things like auditing or tracking user activity.

In addition to being unique, Discord Snowflake IDs are also very large.
With 64 bits of information, there are over 18 quintillion possible Snowflake IDs, meaning it is extremely unlikely that two objects will have the same ID.
This makes Snowflake IDs a reliable and secure way to identify and track objects within Discord.

While most users will not need to worry about Snowflake IDs, they can be useful for developers who are working with the Discord API.
The API provides various methods for retrieving and manipulating objects based on their Snowflake ID,
allowing developers to create custom bots and integrations that can interact with Discord in a variety of ways.

Overall, the Discord Snowflake ID system is an important and integral part of how Discord operates.
It allows Discord to uniquely identify and track objects within the platform, ensuring that everything runs smoothly and efficiently.

.. raw:: latex

    \newpage


**Snowflake structure:**

+---------------------+----------+-----------+------------------------------------------------------------------------------------------------+
|        Field        |   Bits   | Num. bits |                                         Description                                            |
+=====================+==========+===========+================================================================================================+
| Timestamp           | 63 to 22 | 42 bits   | Milliseconds since Discord Epoch, the first second of 2015 or 1420070400000.                   |
+---------------------+----------+-----------+------------------------------------------------------------------------------------------------+
| Internal worker ID  | 21 to 17 | 5 bits    |                                                                                                |
+---------------------+----------+-----------+------------------------------------------------------------------------------------------------+
| Internal process ID | 16 to 12 | 5 bits    |                                                                                                |
+---------------------+----------+-----------+------------------------------------------------------------------------------------------------+
| Increment           | 11 to 0  | 12 bits   | For every ID that is generated on that process, this number is incremented snowflake & 0xFFF   |
+---------------------+----------+-----------+------------------------------------------------------------------------------------------------+

The snowflake can be obtained for each resource through the Discord client by enabling `Developer mode`_ 
and then right clicking on wanted resource and left clicking *"Copy ID"*.

.. raw:: latex

    \newpage


Discord API
=================
The core that the Discord client runs on is the Discord API.

The Discord API allows developers to create applications that interact with the voice and chat platform through two main layers:

- a HTTPS/REST API for general operations such as :
  
  - sending messages,
  - creating channels,
  - fetching information about a channel,
  - joining a voice channel,
  - ...

- and a persistent secure WebSocket connection for real-time events such as:
  
  - new user joins the guild,
  - channel is created / deleted,
  - a new message is sent to a channel,
  - reaction was added to a message,
  - ...

OAuth2 API can also be used to provide access to a platform or service through the Discord API.

.. raw:: latex

    \newpage


Authentication
-----------------
The authentication though the API is performed with the ``Authorization`` header inside
the HTTP request header in the following ways:

1. User accounts:
    ``Authorization: TOKEN``
2. Bots:
    ``Authorization: Bot TOKEN``
3. External applications (OAuth2):
    ``Authorization: Bearer TOKEN``

.. Caution::

    Using the API on **user** accounts outside the Discord client is against ToS.


Status codes
---------------
When making an API request to Discord, it is important to check the status code of the response to ensure that the request was successful.
If the status code is in the 2xx range, it indicates that the request was successful.
If the status code is in the 4xx range, it indicates that there was an error with the request, such as a missing parameter or an unauthorized request.
If the status code is in the 5xx range, it indicates that there was an error on the server side.

In addition to the standard HTTP error code, the Discord API can also return more detailed error codes through the "code" key in the JSON error response.
This response will also include a "message" key with a user-friendly error string.
Some of these errors may include additional details in the form of error messages provided by an "errors" object.

Some codes include:

- 10003: Unknown channel,
- 30001: Maximum number of guilds reached (100),
- 40001: Unauthorized. Provide a valid token and try again.

Full list of error codes is available on the `API Reference`_ .


Discord rate limiting
----------------------

Rate limiting is a technique used to control the amount of incoming and outgoing traffic to or from a network, server, or application.
It is used to prevent overloading of resources, protect against denial of service (DoS) attacks,
and ensure that a system remains available and responsive to legitimate requests.

Discord has implemented rate limits on its APIs to prevent spam, abuse, and server overload.
These limits apply to both individual users and bots and can be based on a specific route or for all requests made.
Some routes have specific rate limits that may also vary depending on the HTTP method used (such as GET, POST, PUT, or DELETE).
In some cases, rate limits for similar routes may be grouped together, as indicated in the X-RateLimit-Bucket response header.
This header can be used as a unique identifier to group shared limits.

During the calculation of rate limits, some routes take into account the top-level resources within the path, such as the guild_id when calling /guilds/{guild.id}/channels.
Currently, the top-level resources that are limited include channels (identified by the channel_id), guilds (identified by the guild_id),
and webhooks (identified by the webhook_id or webhook_id + webhook_token).
This means that if two different top-level resources are used in the same endpoint, the rate limits for those resources will be calculated separately.
For example, if a rate limit is reached when calling the endpoint /channels/1234, it would still be possible to call another endpoint such as /channels/9876 without hitting the limit.

In addition to per-route limits, global rate limits also exist and apply to the total number of requests made by a user or bot, regardless of the specific route.

The API also returns an optional header in the response that tells the bot, how many requests can still be be made, without
triggering the rate limit. The header is called ``X-RateLimit-Remaining``. 
This header is NOT returned if the authorization token used, belongs to an user account.

If the rate limit is exceeded (from making too many requests), then a HTTP status of 429 is returned in the response.
The data returned when the response features 429 status is a JSON dictionary:

+-------------+---------+-------------------------------------------------------------------+
|    Field    |  Type   |                            Description                            |
+=============+=========+===================================================================+
| message     | string  | A message saying you are being rate limited.                      |
+-------------+---------+-------------------------------------------------------------------+
| retry_after | float   | The number of seconds to wait before submitting another request.  |
+-------------+---------+-------------------------------------------------------------------+
| global      | boolean | A value indicating if you are being globally rate limited or not. |
+-------------+---------+-------------------------------------------------------------------+

