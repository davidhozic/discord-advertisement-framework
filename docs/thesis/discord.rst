===================
Discord
===================
This chapter contains some background information on Discord, including how it came to be and some basic information on how it works.
It should give the reader basic background that is needed to understand the rest of the content of the thesis project.


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
