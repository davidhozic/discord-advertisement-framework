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

.. raw:: latex

    \newpage


.. list-table:: Snowflake structure:
    :header-rows: 1


    * 
        - Field
        - Bits
        - Num. bits
        - Description
    *
        - Timestamp
        - 63 to 22
        - 42
        - Milliseconds since Discord Epoch, the first second of 2015 or 1420070400000.
    *
        - Internal worker ID 
        - 21 to 17
        - 5 bits
        -
    *
        - Internal process ID
        - 16 to 12 bits
        - 5 bits
        -
    *
        - Increment
        - 11 to 0
        - 12 bits
        - For every ID that is generated on that process, this number is incremented snowflake & 0xFFF


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



Shilling to Discord
==========================
Like explained in the :ref:`Shilling` chapter, shilling is a type of advertising.
It can be advertised to Discord either manually or automatically.


Manual shilling
---------------------
Manual shilling involves writing your advertisement, creating an account / accounts, finding the servers and then simply posting
into the channels that are meant for it or finding the users to DM about your product.


Generating shill content
^^^^^^^^^^^^^^^^^^^^^^^^^^
You can generate the advertisement content either manually from the top of your head, or
use some more sophisticated methods like AI. A great example of AI tools would be GPT-3 (Generative Pre-trained Transformer 3).

GPT-3 (Generative Pre-training Transformer 3) is a state-of-the-art artificial intelligence language model developed by OpenAI.
It has the ability to generate human-like text and perform a variety of tasks, such as translation, summarization, and question answering.
GPT-3 is the largest and most powerful language model to date, with a capacity of 175 billion parameters. 
It has garnered attention from both researchers and industry professionals due to its impressive capabilities and potential applications.

For reference, the above paragraph was written using Chat GPT.

To generate your advertisement content, you would, for example, pass GPT-3 with the following input:

*"Write advertisement for my White Rabbit NFT project which came out in 2023. 
We have over 9000 different NFT available for purchase. Talk about the limited Gray Rabbit NFT (only 50 available). Get additional information here www.mynft.domain"*

and it would generate: 

*"Attention all NFT collectors and art enthusiasts!
We are excited to announce the launch of our White Rabbit NFT project, featuring over 9000 unique and one-of-a-kind digital art pieces. But that's not all - we have a special edition of limited Gray Rabbit NFTs available for purchase, with only 50 available worldwide.
Don't miss out on the opportunity to own a piece of digital art history. These Gray Rabbit NFTs are sure to become highly sought after and increase in value over time.
But act fast - there are only 50 available, and once they're gone, they're gone for good.
For more information and to purchase your own Gray Rabbit NFT, visit www.mynft.domain. Don't wait - add one of these rare and valuable NFTs to your collection today!"*

Once you have the advertisement content, you would just copy and paste it to each channel.

.. figure:: images/chatgpt.png
    :width: 400

    Chat GPT (GPT-3) example


Finding guilds to shill into
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Once you have your advertisement content, you need to find your guilds, that you want to shill into.
A good place to find the servers would be simply searching the web for websites that have a list of different
servers and allows searching for guilds by name / category.

A good example for finding guilds (servers), would actually be Discord itself, as they hold a list of certain servers, but for a server to be eligible 
for discovery on Discord, it needs to have at least 1000 members, meaning that the servers you can join directly from Discord's website, 
probably have some protection against shilling and they probably don't allow it.

Another, probably better, example would be website `Top.GG <https://top.gg>`_, which besides holding a list of servers,
also holds a list of public Discord bots, but that is not relevant for the purposes of this thesis.
Top.gg has a search bar with various parameters you can use to find your servers, to find NFT servers, it can be used
to simply search for "NFT".

After finding all the guilds, you would join all the guilds and find the channels appropriate to shill into
(without the owners kicking / banning you). These channels are usually named *shill, shilling, advertising, self-promo, ...*.

.. figure:: images/topgg_find_servers.png
    :width: 400

    Top.GG server discovery

