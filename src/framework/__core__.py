"""
    DISCORD SHILLING FRAMEWORK (DSF)
    Author      :: David Hozic
    Copyright   :: Copyright (c) 2022 David Hozic
    Version     :: V1.7.6
"""
from   contextlib import suppress
from   typing import Union, List
import time
import asyncio
import random
import os
import enum
import pycordmod as discord
import datetime
import copy


#######################################################################
# Exports
#######################################################################
__all__ = (    # __all__ variable dictates which objects get imported when using from <module> import *                                 
    "discord",
    "C_DAY_TO_SECOND",
    "C_HOUR_TO_SECOND",
    "C_MINUTE_TO_SECOND",
    "GUILD",
    "MESSAGE",
    "FILE",
    "EMBED",
    "EMBED_FIELD",
    "run",
    "data_function",
    "get_client",
)

#######################################################################
# Globals   (These are all set in the framework.run function)
#######################################################################
m_user_callback          = None     # User provided function to call after framework is ready
m_server_log_output_path = None     # User provided for server log output path
m_server_list            = None     # User provided server list
m_debug                  = None     # User provided option to enable debugging
m_client                 = None     # Pycord Client object

#######################################################################
# Contants
#######################################################################
C_DAY_TO_SECOND = 86400
C_HOUR_TO_SECOND= 3600
C_MINUTE_TO_SECOND = 60

#######################################################################
# Debugging
#######################################################################
class TRACE_LEVELS(enum.Enum):
    """
    Info: Level of trace for debug
    """
    NORMAL = 0
    WARNING = 1
    ERROR =  2

def trace(message: str,
          level:   TRACE_LEVELS = TRACE_LEVELS.NORMAL):
    """"
    Name : trace
    Param:
    - message : str          = Trace message
    - level   : TRACE_LEVELS = Level of the trace
    """
    if m_debug:
        l_timestruct = time.localtime()
        l_timestamp = "Date: {:02d}.{:02d}.{:04d} Time:{:02d}:{:02d}"
        l_timestamp = l_timestamp.format(l_timestruct.tm_mday,
                                         l_timestruct.tm_mon,
                                         l_timestruct.tm_year,
                                         l_timestruct.tm_hour,
                                         l_timestruct.tm_min)
        l_trace = f"{l_timestamp}\nTrace level: {level.name}\nMessage: {message}\n"
        print(l_trace)


#######################################################################
# Decorators
#######################################################################
class __FUNCTION_CLS_BASE__:
    """
    type: dummy class
    name: __FUNCTION_CLS_BASE__
    info: used as a base class to __FUNCTION_CLS__ which gets created in framework.data_function decorator.
    Because the __FUNCTION_CLS__ is inaccessible outside the data_function decorator, this class is used to detect
    if the MESSAGE.data parameter is of function type, because the function isinstance also returns True when comparing
    the object to it's class or to the base class from which the object class is inherited from.
    """

def data_function(fnc):
    """
    type:   Decorator
    name:   data_function
    info:   Decorator used to create a framework __FUNCTION_CLS__ class for function
    return: __FUNCTION_CLS__
    """
    class __FUNCTION_CLS__(__FUNCTION_CLS_BASE__):
        """"
        _FUNCTION_CLS_
        Info : Used for creating special classes that are then used to create objects in the framework.MESSAGE
               data parameter, allows for sending dynamic contentent received thru an user defined function.

        Param: function
        """
        __slots__ = (
            "args",
            "kwargs",
            "func_name",
        )

        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs
            self.func_name = fnc.__name__

        def get_data(self):
            """
            Retreives the data from the user function
            """
            return fnc(*self.args, **self.kwargs)
    return __FUNCTION_CLS__


#######################################################################
# Misc. classes
#######################################################################
class TIMER:
    """
    TIMER
    Info : Used in MESSAGE objects as a send timer
    """
    __slots__ = (
        "running",
        "startms"
    )

    def __init__(self):
        "Initiate the timer"
        self.running = False
        self.startms = 0
    def start(self):
        "Start the timer"
        if self.running:
            return True
        self.running = True
        self.startms = time.time()
        return False
    def elapsed(self):
        "Return the timer elapsed from last reset"
        return time.time() - self.startms if self.running else 0
    def reset (self):
        "Reset the timer"
        self.running = False

#######################################################################
# Framework classes
#######################################################################
class CLIENT(discord.Client):
    """
        Name : CLIENT
        Info : Inherited class from discord.Client.
               Contains an additional on_ready function.
    """
    async def on_ready(self):
        """
        Name : on_ready
        Info : Tasks that is started by pycord when you have been successfully logged into discord.
        """
        trace(f"Logged in as {self.user}", TRACE_LEVELS.NORMAL)

        if initialize():
            # Initialization was successful, so create the advertiser task and start advertising.
            trace("Successful initialization!",TRACE_LEVELS.NORMAL)
            asyncio.gather(asyncio.create_task(advertiser()))
        else:
            # Initialization failed, close everything
            await m_client.close()

        if m_user_callback:   # If user callback function was specified
            m_user_callback() # Call user provided function after framework has started


class EMBED_FIELD:
    """
    Embedded field class for use in EMBED object constructor
    Parameters:
    -  Name         : str    -- Name of the field
    -  Content      : str    -- Content of the embedded field
    -  Inline       : bool   -- Make this field appear in the same line as the previous field
    """
    def __init__(self,
                 name : str,
                 content : str,
                 inline : bool=False):
        self.name = name
        self.content = content
        self.inline = inline

    def __iter__(self):
        """
        Name: __iter__
        Info: Iterator used to return EMBED_FIELD_ITER
        """
        class EMBED_FIELD_ITER:
            """
            Name: EMBED_FIELD_ITER
            Info: Iterator used to expand the EMBED_FIELD object into name, content, inline
            """
            def __init__(self, data):
                self.__data = data
                self.__index = 0
                self.__max = len(data)
            def __next__(self):
                if self.__index == self.__max:
                    raise StopIteration
                self.__index +=1
                return self.__data[self.__index-1]
        return EMBED_FIELD_ITER([self.name, self.content, self.inline])


class EMBED(discord.Embed):
    """
    Derrived class of discord.Embed with easier definition
    Parameters:
        Added parameters:
            - author_name       : str           -- Name of embed author
            - author_icon       : str           -- Url to author image
            - image             : str           -- Url of image to be placed at the end of the embed
            - thumbnail         : str           -- Url of image that will be placed at the top right of embed
            - fields            : list          -- List of EMBED_FIELD objects
        Inherited from discord.Embed:
            - For the other, original params see https://docs.pycord.dev/en/master/api.html?highlight=discord%20embed#discord.Embed

    """
    __slots__ = (
        'title',
        'url',
        'type',
        '_timestamp',
        '_colour',
        '_footer',
        '_image',
        '_thumbnail',
        '_video',
        '_provider',
        '_author',
        '_fields',
        'description',
    )
    # Static members
    Color = Colour = discord.Color  # Used for color parameter
    EmptyEmbed = discord.embeds.EmptyEmbed

    @staticmethod
    def from_discord_embed(_object : discord.Embed):
        """
        Name:   from_discord_embed
        Type:   static method
        Param:
            - object : discord.Embed | discord.Embed (same type) -- The discord Embed object you want converted into the framework.EMBED class
        """

        ret = EMBED()
        # Copy attributes but not special methods to the new EMBED. "dir" is used instead of "vars" because the object does not support the function.
        for key in dir(_object):
            if not key.startswith("__") and not key.endswith("__"):
                with suppress(Union[AttributeError,TypeError]):
                    if not callable(getattr(_object, key)) and not isinstance(getattr(_object.__class__, key), property):
                        setattr(ret, key, copy.deepcopy(getattr(_object,key)))


        return ret

    # Object members
    def __init__(self, *,
                # Additional parameters
                author_name: str=None,
                author_icon: str=EmptyEmbed,
                image: str= None,
                thumbnail : str = None,
                fields : List[EMBED_FIELD] = None,
                # Base class parameters
                colour: Union[int, Colour] = EmptyEmbed,
                color: Union[int, Colour] = EmptyEmbed,
                title: str = EmptyEmbed,
                type :str = "rich",
                url: str= EmptyEmbed,
                description = EmptyEmbed,
                timestamp: datetime.datetime = None):

        ## Initiate original arguments from discord. Embed
        ## by looping thru the super().__init__ annotations(variables the function accepts)
        base_args = {}
        localargs = locals()
        for key in super().__init__.__annotations__:
            base_args[key] = localargs[key]
        super().__init__(**base_args)

        ## Set author
        if author_name is not None:
            self.set_author(name=author_name, icon_url=author_icon)
        ## Set image
        if image is not None:
            self.set_image(url=image)
        ## Set thumbnail
        if thumbnail is not None:
            self.set_thumbnail(url=thumbnail)
        ### Set fields
        if fields is not None:
            for field_name, content, inline in fields:
                self.add_field(name=field_name,value=content,inline=inline)


class FILE:
    """
    Name: FILE
    Info: FILE object used as a data parameter to the MESSAGE objects.
          This is needed aposed to a normal file object because this way,
          you can edit the file after the framework has already been started.
    """
    __slots__ = ("filename",)
    def __init__(self,
                 filename):
        self.filename = filename
        # Try to open file before framework starts for easier exception debug
        with open(filename, "rb") as reader:
            pass


class MESSAGE:
    """
    Name: MESSAGE
    Info: The MESSAGE object containts parameters which describe behaviour and data that will be sent to the channels.
    Params:
    - Start Period , End Period (start_period, end_period) - These 2 parameters specify the period on which the messages will be sent:
    Start Period can be either:
        - None - Messages will be sent on intervals specified by End period,
        - Integer >= 0 - Messages will be sent on intervals randomly chosen between Start period and End period,
          where the randomly chosen intervals will be re-randomized after each sent message.
    - Data (data) - The data parameter is the actual data that will be sent using discord's API. The data types of this parameter can be:
        - String (normal text),
        - framework.EMBED,
        - framework.FILE,
        - List/Tuple containing any of the above arguments (There can up to 1 string, up to 1 embed and up to 10 framework.FILE objects,
          if more than 1 string or embeds are sent, the framework will only consider the last found).
        - Function that accepts any amount of parameters and returns any of the above types.
          To pass a function, YOU MUST USE THE framework.data_function decorator on the function before passing the function to the framework.
    - Channel IDs (channel_ids) - List of IDs of all the channels you want data to be sent into.
    - Clear Previous (clear_previous) - A bool variable that can be either True of False. If True, then before sending a new message to the channels,
      the framework will delete all previous messages sent to discord that originated from this message object.
    - Start Now (start_now) - A bool variable that can be either True or False. If True, then the framework will send the message
      as soon as it is run and then wait it's period before trying again. If False, then the message will not be sent immediatly after framework is ready,
      but will instead wait for the period to elapse.
    """
    __slots__ = (
        "randomized_time",
        "period",
        "random_range",
        "data",
        "channels",
        "timer",
        "clear_previous",
        "force_retry",
        "sent_msg_objs"
    )

    def __init__(self,
                start_period : Union[float,None],
                end_period : float,
                data : Union[str, EMBED, FILE, List[Union[str, EMBED, FILE]]],
                channel_ids : List[int],
                clear_previous : bool,
                start_now : bool):

        if start_period is None:            # If start_period is none -> period will not be randomized
            self.randomized_time = False
            self.period = end_period
        else:
            self.randomized_time = True
            self.random_range = (start_period, end_period)
            self.period = random.randrange(*self.random_range)  # This will happen after each sending as well

        self.data = data
        self.channels = channel_ids
        self.timer = TIMER()
        self.clear_previous = clear_previous
        self.force_retry = {"ENABLED" : start_now, "TIME" : 0}
        self.sent_msg_objs = []

class GUILD:
    """
    Name: GUILD
    Info: The GUILD object represents a server to which messages will be sent.
    Params:
    - Guild ID - identificator which can be obtained by enabling developer mode in discord's settings and
                 afterwards right-clicking on the server/guild icon in the server list and clicking "Copy ID",
    - List of MESSAGE objects - Python list or tuple contating MESSAGE objects.
    - Generate file log - bool variable, if True it will generate a file log for each message send attempt.
    """
    __slots__ = (
        "guild",
        "messages",
        "_generate_log",
        "guild_file_name"
    )

    def __init__(self,
                 guild_id : int,
                 messages_to_send : List[MESSAGE],
                 generate_log : bool = False):

        self.guild =    guild_id
        self.messages = messages_to_send
        self._generate_log = generate_log
        self.guild_file_name = None

    def generate_log(self,
                      sent_text : str,
                      sent_embed : discord.Embed,
                      sent_files : list,
                      succeeded_ch : list,
                      failed_ch : list):
        """
        Name: generate_log
        Info: Generates a log of a message send attempt
        """
        # Generate text
        sent_text = "\t```\n".join(f"\t{line}\n" for line in sent_text.splitlines(keepends=True)) + "\t```" if sent_text is not None else ""
        #Generate embed
        EmptyEmbed = discord.embeds.EmptyEmbed
        ets = sent_embed.timestamp
        tmp_emb = sent_embed
        if tmp_emb is not None:
            sent_embed = \
f"""
Title:        {tmp_emb.title if tmp_emb.title is not EmptyEmbed else ""}
Author:       {tmp_emb.author.name if tmp_emb.author.name is not EmptyEmbed else ""}
Thumbnail:    {tmp_emb.thumbnail.url if tmp_emb.thumbnail.url is not EmptyEmbed else ""}
Image:        {tmp_emb.image.url if tmp_emb.image.url is not EmptyEmbed else ""}
Description:  {tmp_emb.description if tmp_emb.description is not EmptyEmbed else ""}
Color:        {tmp_emb.colour if tmp_emb.colour is not EmptyEmbed else ""}
Timestamp:    {f"{ets.day}.{ets.month}.{ets.year}  {ets.hour}:{ets.minute}:{ets.second}" if ets is not EmptyEmbed else ""}
"""
            sent_embed += "\nFields:"
            for field in tmp_emb.fields:
                sent_embed += f"\n - {field.name}\n"
                sent_embed += "\t```\n"
                for line in field.value.splitlines():
                    sent_embed += f"\t{line}\n"
                sent_embed += "\t```"

        else:
            sent_embed = ""

        # Generate timestamp
        l_timestruct = time.localtime()
        l_timestamp = "{:02d}.{:02d}.{:04d} {:02d}:{:02d}".format(l_timestruct.tm_mday,
                                                                  l_timestruct.tm_mon,
                                                                  l_timestruct.tm_year,
                                                                  l_timestruct.tm_hour,
                                                                  l_timestruct.tm_min)
        # Generate channel log
        succeeded_ch = "[\n" + "".join(f"\t\t{ch.name}(ID: {ch.id}),\n" for ch in succeeded_ch).rstrip(",\n") + "\n\t]" if len(succeeded_ch) else "[]"
        failed_ch = "[\n"+ "".join(f"\t\t- {channel['channel'].name}(ID: {channel['channel'].id}) >>> Reason: {channel['reason']},\n" for channel in failed_ch).rstrip(",\n") + "\n\t]" if len(failed_ch) else "[]"
            
        # Generate files
        sent_files = "".join(    f"- ```\n  {file}\n  ```\n" for file in sent_files    ).rstrip("\n")

        return f'''
# MESSAGE LOG:
## Text:
{sent_text}
## Embed fields:
{sent_embed}
## Files:
{sent_files}
## Other data:
-   ```
    Server: {self.guild.name}
    Succeeded in channels: {succeeded_ch}
    Failed in channels: {failed_ch}
    Timestamp: {l_timestamp}
    ```
***
'''

    async def advertise(self):
        """
        Name: advertise
        Info: async function that goes thru all the messages inside the guild and tries to send them to discord
              if timer has reached the expected value.
        """
        l_trace = ""
        if self.guild is not None:
            for l_msg in self.messages:
                if l_msg.timer.start() and\
                   (not l_msg.force_retry["ENABLED"] and l_msg.timer.elapsed() > l_msg.period\
                    or l_msg.force_retry["ENABLED"] and l_msg.timer.elapsed() > l_msg.force_retry["TIME"]) :  # If timer has started and timer is above set period/above force_retry period
                    l_msg.timer.reset()
                    l_msg.timer.start()
                    l_msg.force_retry["ENABLED"] = False
                    if l_msg.randomized_time is True:           # If first parameter to msg object is not None
                        l_msg.period = random.randrange(*l_msg.random_range)

                    # Parse data from the data parameter
                    l_data_to_send  = None
                    if isinstance(l_msg.data, __FUNCTION_CLS_BASE__):
                        l_data_to_send = l_msg.data.get_data()
                    else:
                        l_data_to_send = l_msg.data

                    l_embed_to_send = None
                    l_text_to_send  = None
                    l_files_to_send  = []
                    # If any valid data was passed to the data parameter of framework.MESSAGE
                    if l_data_to_send is not None:
                        # Convert into a regular list
                        l_data_to_send = l_data_to_send if isinstance(l_data_to_send, Union[list, tuple, set]) else [l_data_to_send]
                        for element in l_data_to_send:
                            if isinstance(element, str):
                                l_text_to_send = element

                            elif isinstance(element, EMBED):
                                l_embed_to_send = element

                            elif isinstance(element, FILE):
                                l_file = discord.File(element.filename)
                                l_files_to_send.append(l_file)

                            elif element is not None:
                                trace(f"INVALID DATA PARAMETER PASSED!\nArgument is of type : {type(element).__name__}\nSee README.md for allowed data types\nGUILD: {self.guild.name} (ID: {self.guild.id})",
                                      TRACE_LEVELS.WARNING)

                    # Send messages
                    if l_text_to_send is not None or l_embed_to_send is not None or len(l_files_to_send) > 0:
                        l_errored_channels = []
                        l_succeded_channels= []

                        ## Clear previous msgs
                        if l_msg.clear_previous:
                            for l_sent_msg_obj in l_msg.sent_msg_objs:
                                try:
                                    await l_sent_msg_obj.delete()
                                except discord.HTTPException as ex:
                                    if ex.status == 429:
                                        await asyncio.sleep(int(ex.response.headers["Retry-After"])+1)

                            l_msg.sent_msg_objs.clear()

                        # Send to channels
                        for l_channel in l_msg.channels:
                            for tries in range(3):  # Maximum 3 tries (if rate limit)
                                try:
                                    # SEND TO CHANNEL
                                    l_discord_sent_msg = await l_channel.send(l_text_to_send,
                                                                              embed=l_embed_to_send,
                                                                              files=l_files_to_send)

                                    l_succeded_channels.append(l_channel)
                                    if l_msg.clear_previous:
                                        l_msg.sent_msg_objs.append(l_discord_sent_msg)

                                    break    # Break out of the tries loop
                                except Exception as ex:
                                    # Failed to send message
                                    if isinstance(ex, discord.HTTPException) and ex.status == 429:
                                        # the if sentence is evaluated by short circuit evaluation
                                        retry_after = int(ex.response.headers["Retry-After"])  + 1
                                        # Slow Mode detected -> wait the remaining time
                                        if ex.code == 20026:
                                            l_msg.force_retry["ENABLED"] = True
                                            l_msg.force_retry["TIME"] = retry_after
                                        else:
                                            # Rate limit but not slow mode -> put the framework to sleep as it won't be able to send any messages globaly
                                            trace(f"Rate limit! Retrying after {retry_after}",TRACE_LEVELS.WARNING)
                                            await asyncio.sleep(retry_after)

                                    if tries == 2 or not isinstance(ex, discord.HTTPException) or\
                                       ex.status != 429 or ex.code == 20026:
                                        l_errored_channels.append({"channel":l_channel, "reason":ex})
                                        break

                        l_trace += self.generate_log(l_text_to_send, l_embed_to_send, [x.filename for x in l_files_to_send], l_succeded_channels, l_errored_channels)     # Generate trace of sent file
            # Save into file
            if self._generate_log and l_trace:
                with suppress(FileExistsError):
                    os.mkdir(m_server_log_output_path)
                with open(os.path.join(m_server_log_output_path, self.guild_file_name),'a', encoding='utf-8') as l_logfile:
                    l_logfile.write(l_trace)


#######################################################################
# Tasks
#######################################################################
async def advertiser():
    """
    Name  : advertiser
    Param : void
    Info  : Main task that is responsible for the framework
    """
    while True:
        await asyncio.sleep(0.100)
        for l_server in m_server_list:
            await l_server.advertise()


#######################################################################
# Functions
#######################################################################
def initialize() -> bool:
    """
    Name: initialize
    Parameters: void
    Return: success: bool
    Info: Function that initializes the guild objects and then returns True on success or False on failure.
    """
    for l_server in m_server_list[:]:
        """
        Replace the guild IDs with actual discord.Guild objects or remove if any errors were discovered.
        The m_server_list is sliced (shallow copied) to allow item
        removal from the list while still under the for loop (the iterator will
        return items from the copied list by reference and I remove them from original list).
        """
        l_guild_id = l_server.guild
        l_server.guild = m_client.get_guild(l_guild_id)

        if l_server.guild is not None:
        # Create a file name without the non allowed characters. Windows' list was choosen to generate the forbidden character because only forbids '/'
            l_forbidden_file_names = ('<','>','"','/','\\','|','?','*',":")
            l_server.guild_file_name = "".join(char if char not in l_forbidden_file_names else "#" for char in l_server.guild.name) + ".md"

            for l_msg in l_server.messages[:]:
                """
                Initialize all the MESSAGE objects -- Replace all the channel IDs with actual channel objects.
                Slice (shallow copy) the messages array to allow removal of message objects without affecting the iterator.
                """

                # Transform channel ids into pycord channel objects
                l_channel_i = 0
                while l_channel_i < len(l_msg.channels):
                    """
                    Replace the channel IDs with channel objects.
                    while loop is used as I don't want the index to increase every iteration
                    """
                    l_channel_id = l_msg.channels[l_channel_i]
                    l_msg.channels[l_channel_i] = m_client.get_channel(l_channel_id)
                    l_channel = l_msg.channels[l_channel_i]

                    if l_channel is None:
                        # Unable to find the channel objects, ergo remove.
                        trace(f"Unable to get channel from id: {l_channel_id} (Does not exist - Incorrect ID?) in GUILD: \"{l_server.guild.name}\" (ID: {l_guild_id})", TRACE_LEVELS.WARNING)
                        l_msg.channels.remove(l_channel)

                    elif l_channel.guild.id != l_guild_id:
                        # The channel is not part of this guild, ergo remove.
                        trace(f"Guild \"{l_server.guild.name}\" (ID: {l_guild_id}) has no channel \"{l_channel.name}\" (ID: {l_channel_id})", TRACE_LEVELS.WARNING)
                        l_msg.channels.remove(l_channel)
                    else:
                        l_channel_i += 1

                # Check for correct data types of the MESSAGE.data parameter
                if not isinstance(l_msg.data, __FUNCTION_CLS_BASE__):
                    # Convert any arguments passed into a list of arguments
                    if  isinstance(l_msg.data, Union[list, tuple, set]):
                        l_msg.data = list(l_msg.data)   # Convert into a regular list to allow removal of items
                    else:
                        l_msg.data = [l_msg.data]

                    # Check all the arguments
                    for l_data in l_msg.data[:]:
                        """
                        Check all the data types of all the passed to the data parameter.
                        If class does not match the allowed types, then the object is removed.
                        The for loop iterates thru a shallow copy (sliced list) of l_data_params to allow removal of items
                        without affecting the iteration (would skip elements without a copy or use of while loop)
                        """
                        if (
                            not isinstance(l_data, str) and\
                            not isinstance(l_data, EMBED) and\
                            not isinstance(l_data, FILE)\
                        ):
                            if isinstance(l_data, __FUNCTION_CLS_BASE__):
                                trace(f"The function can only be used on the data parameter directly, not in a list\nFunction: {l_data.func_name}", TRACE_LEVELS.ERROR)
                                l_msg.data.clear()
                                break
                            else:
                                trace(f"INVALID DATA PARAMETER PASSED!\nArgument is of type : {type(l_data).__name__}\nSee README.md for allowed data types\nGUILD: {l_server.guild.name} (ID: {l_server.guild.id})", TRACE_LEVELS.WARNING)
                                l_msg.data.remove(l_data)


                # Check if any data params are left and remove the message object if not
                if (not len(l_msg.channels) or
                    not isinstance(l_msg.data, __FUNCTION_CLS_BASE__) and not len(l_msg.data)   # if isinstance __FUNCTION_CLS_BASE__, then it has no len, and because of short-circuit, len will not be read
                ):
                    """
                    Failed parsing of all the channels
                    or/and all the data parameters inside the message object, ergo remove the message.
                    """
                    l_server.messages.remove(l_msg)

            if not len(l_server.messages):
                """
                No messages were successfuly processed,
                ergo remove the guild object from the list as it is useless.
                Trace is silent since it is already made in the deepest level of these checks.
                """
                m_server_list.remove(l_server)

        else:
            trace(f"Unable to create server object from server id: {l_guild_id}\nRemoving the object from the list!", TRACE_LEVELS.WARNING)
            m_server_list.remove(l_server)

    if len(m_server_list):
        return True
    else:
        trace("No guilds could be parsed", TRACE_LEVELS.ERROR)
        return False


def get_client():
    """
    Name:   get_client
    Params: void
    Return: discord.Client | None
    Info:   Returns the client object used by the framework, so the user wouldn't have to run 2 clients.
    """
    return m_client


def run(token : str,
        server_list : List[GUILD],
        is_user : bool =False,
        user_callback : bool=None,
        server_log_output : str ="History",
        debug : bool=True):
    """
    @type  : function
    @name  : run
    @params:
        - token             : str       = access token for account
        - server_list       : list      = List of framework.GUILD objects
        - is_user           : bool      = Set to True if token is from an user account and not a bot account
        - user_callback     : function  = User callback function (gets called after framework is ran)
        - server_log_output : str       = Path where the server log files will be created
        - debug             : bool      = Print trace message to the console,
                                          useful for debugging if you feel like something is not working

    @description: This function is the function that starts framework and starts shilling
    """
    global m_user_callback,\
           m_server_log_output_path,\
           m_server_list,\
           m_debug,\
           m_client

    m_client = CLIENT()
    m_server_log_output_path = server_log_output    ## Path to folder where to crete server logs
    m_debug = debug                                 ## Print trace messages to the console for debugging purposes
    m_server_list = server_list                     ## List of guild objects to iterate thru in the advertiser task
    m_user_callback = user_callback                 ## Called after framework has started

    if is_user:
        trace("Bot is an user account which is against discord's ToS",TRACE_LEVELS.WARNING)
    m_client.run(token, bot=not is_user)
