"""
    DISCORD SHILLING FRAMEWORK (DSF)
    Author      :: David Hozic
    Copyright   :: Copyright (c) 2022 David Hozic
    Version     :: V1.7.4.1
"""
from contextlib import suppress
from   typing import Union, List
import time
import asyncio
import random
import types
import os
import enum
import pycordmod as discord
import datetime

#######################################################################
# Globals
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

def TRACE(message: str,
          level:   TRACE_LEVELS):
    """"
    Name : TRACE
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
# Tasks
#######################################################################
async def advertiser():
    """
    Name  : advertiser
    Param : void
    Info  : Main task that is responsible for the framework
    """
    if not m_server_list:
        TRACE("SERVER LIST IS NOT DEFINED!", TRACE_LEVELS.ERROR)
    for l_server in m_server_list:
        await l_server.initialize()
    while True:
        await asyncio.sleep(0.100)
        for l_server in m_server_list:
            await l_server.advertise()

#######################################################################
# Decorators
#######################################################################
class __FUNCTION_CLS_BASE__:
    """
    type: dummy class
    name: __FUNCTION_CLS_BASE__
    info: used as a base class to __FUNCTION_CLS__ which gets created in framework.FUNCTION decorator.
    Because the __FUNCTION_CLS__ is inaccessible outside the FUNCTION decorator, this class is used to detect
    if the MESSAGE.data parameter is of function type, because the function isinstance also returns True when comparing
    the object to it's class or to the base class from which the object class is inherited from.
    """

def FUNCTION(fnc):
    """
    type:   Decorator
    name:   FUNCTION
    info:   Decorator used to create a framework __FUNCTION_CLS__ class for function
    return: __FUNCTION_CLS__
    usage:  \n\n@framework.FUNCTION\ndef function(a,b,c)\n\treturn [str | embed | file | list | tuple]
    """
    class __FUNCTION_CLS__(__FUNCTION_CLS_BASE__):
        """"
        _FUNCTION_CLS_
        Info : Used for creating special classes that are then used to create objects in the framework.MESSAGE
               data parameter, allows for sending dynamic contentent received thru an user defined function.

        Param: function
        """
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs
            
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
class DISCORD_CLIENT(discord.Client):
    """
        Name : DISCORD_CLIENT
        Info : Inherited class from discord.Client.
               Contains an additional on_ready function.
    """
    async def on_ready(self):
        """
        Name : on_ready
        Info : Tasks that is started by pycord when you have been successfully logged into discord.
        """
        TRACE(f"Logged in as {self.user}", TRACE_LEVELS.NORMAL)
        asyncio.gather(asyncio.create_task(advertiser()))
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
        return EMBED_FIELD_ITER([self.name, self.content,self.inline])

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
    
    # TODO DOCUMENTATION
    # Static members   
    Color = Colour = discord.Color  # Used for color parameter
    EmptyEmbed = discord.embeds.EmptyEmbed
    pass
    @staticmethod
    def from_discord_embed(object : discord.Embed):
        """
        Name:   from_discord_embed
        Type:   static method
        Param:  
            - object : discord.Embed | discord.Embed (same type) -- The discord Embed object you want converted into the framework.EMBED class
        """
        ret = EMBED()
        with suppress(TypeError):
            for key in dir(object):
                setattr(ret,key, getattr(object,key))                    
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
        
        ## Set original args from discord.Embed
        default_args = {}
        localargs = locals()
        for key, value in super().__init__.__annotations__.items():
            default_args[key] = localargs[key]
        super().__init__(**default_args)

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
    def __init__(self,
                 filename):
        self.filename = filename

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
          To pass a function, YOU MUST USE THE framework.FUNCTION decorator on the function before passing the function to the framework.
    - Channel IDs (channel_ids) - List of IDs of all the channels you want data to be sent into.
    - Clear Previous (clear_previous) - A bool variable that can be either True of False. If True, then before sending a new message to the channels,
      the framework will delete all previous messages sent to discord that originated from this message object.
    - Start Now (start_now) - A bool variable that can be either True or False. If True, then the framework will send the message
      as soon as it is run and then wait it's period before trying again. If False, then the message will not be sent immediatly after framework is ready,
      but will instead wait for the period to elapse.
    """
    def __init__(self,
                start_period : float,
                end_period : float,
                data : Union[str, discord.Embed, list, types.FunctionType, FILE],
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
    - Guild ID - identificator which can be obtain by enabling developer mode in discord's settings and
                 afterwards right-clicking on the server/guild icon in the server list and clicking "Copy ID",
    - List of MESSAGE objects - Python list or tuple contating MESSAGE objects.
    - Generate file log - bool variable, if True it will generate a file log for each message send attempt.
    """
    def __init__(self,
                 guild_id : int,
                 messages_to_send : List[MESSAGE],
                 generate_log : bool = False):

        self.guild =    guild_id
        self.messages = messages_to_send
        self.generate_log = generate_log
        self.guild_file_name = None
    async def initialize(self):       # Get objects from ids
        """
        Name: initialize
        Info: After login to discord, this functions initializes the guild and channel objects
        """
        l_guild_id = self.guild
        self.guild = m_client.get_guild(l_guild_id) # Transofrm guild id into API guild object
        if self.guild is not None:
            for l_msg in self.messages:
                for index in range(len(l_msg.channels)):
                    l_channel_id = l_msg.channels[index]
                    l_msg.channels[index] = m_client.get_channel(l_channel_id)
                    if l_msg.channels[index] is None:
                        TRACE(f"Unable to find channel from id: {l_channel_id}\nIn guild: {self.guild} (ID: {self.guild.id})", TRACE_LEVELS.ERROR)
                while None in l_msg.channels:
                    l_msg.channels.remove(None)

            self.guild_file_name = self.guild.name.replace("/","-").replace("\\","-").replace(":","-").replace("!","-").replace("|","-").replace("*","-").replace("?","-").replace("<","(").replace(">", ")") + ".md"
        else:
            TRACE(f"Unable to create server object from server id: {l_guild_id}\nRemoving the object from the list!", TRACE_LEVELS.ERROR)
            m_server_list.remove(self)
            del self

    def _generate_log(self,
                      sent_text : str,
                      sent_embed : discord.Embed,
                      sent_files : list,
                      succeeded_ch : list,
                      failed_ch : list):
        """
        Name: _generate_log
        Info: Generates a log of a message send attempt
        """
        l_tmp = ""
        if sent_text:
            l_tmp += "-   ```\n"
            for line in sent_text.split("\n"):
                l_tmp += f"\t{line}\n"
            l_tmp += "    ```"
        sent_text = l_tmp
        l_tmp = ""
        if sent_embed:
            for field in sent_embed.fields:
                l_tmp += f"\n- {field.name}\n\t```\n"

                for line in field.value.split("\n"):
                    l_tmp+=f"\t{line}\n"
                l_tmp = l_tmp.rstrip()
                l_tmp += "\n\t```"
        sent_embed = l_tmp
        l_tmp = ""
        if sent_files.__len__():
            l_tmp += "-   ```\n"
            for filename in sent_files:
                l_tmp += f"\t{filename}\n"
            l_tmp += "    ```"
        sent_files = l_tmp
        l_timestruct = time.localtime()
        l_timestamp = "Date:{:02d}.{:02d}.{:04d} Time:{:02d}:{:02d}".format(l_timestruct.tm_mday, l_timestruct.tm_mon, l_timestruct.tm_year,l_timestruct.tm_hour,l_timestruct.tm_min)
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
__________________________________________________________
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
                        if not isinstance(l_data_to_send, Union[list,tuple]):
                            l_data_to_send = [l_data_to_send]
                        # data is list -> parse each element
                        for element in l_data_to_send:
                            if isinstance(element, str):
                                l_text_to_send = element
                            elif isinstance(element, EMBED):
                                l_embed_to_send = element
                            elif isinstance(element, FILE):
                                l_files_to_send.append(discord.File(element.filename))
                            elif element is not None:
                                TRACE(f"""\
                                INVALID DATA PARAMETER PASSED!
                                Argument is of type : {element.__class__}
                                See README.md for allowed data types
                                GUILD: {self.guild.name} (ID: {self.guild.id})
                                """,
                                 TRACE_LEVELS.ERROR)

                    # Send messages
                    if l_text_to_send or l_embed_to_send or l_files_to_send:
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
                                    if l_channel.guild.id != self.guild.id:
                                        TRACE(f"Channel {l_channel.name} (ID: {l_channel.id}) is not part of guild {self.guild.name} (ID: {self.guild.id})",TRACE_LEVELS.ERROR)
                                        l_msg.channels.remove(l_channel)  ## Remove from list as channel not part of the current guild
                                    else:
                                        # SEND TO CHANNEL
                                        l_discord_sent_msg = await l_channel.send(l_text_to_send,
                                                                                  embed=l_embed_to_send,
                                                                                  files=l_files_to_send)
                                        l_succeded_channels.append(l_channel.name)
                                        if l_msg.clear_previous:
                                            l_msg.sent_msg_objs.append(l_discord_sent_msg)
                                    break    # Break out of the tries loop
                                except discord.HTTPException as ex:
                                    # Failed to send message
                                    l_error_text = f"{l_channel.name} - Reason: {ex}"
                                    if ex.status == 429:
                                        retry_after = int(ex.response.headers["Retry-After"])  + 1
                                        # Slow Mode detected -> wait the remaining time
                                        if ex.code == 20026:
                                            l_msg.force_retry["ENABLED"] = True
                                            l_msg.force_retry["TIME"] = retry_after

                                        else:
                                            # Rate limit but not slow mode -> put the framework to sleep as it won't be able to send any messages globaly
                                            TRACE(f"Rate limit! Retrying after {retry_after}",TRACE_LEVELS.WARNING)
                                            await asyncio.sleep(retry_after)

                                        l_error_text += f" - Retrying after {retry_after}"
                                    else:
                                        await asyncio.sleep(0.25)   # Wait a bit before retrying

                                    if tries == 2 or ex.status != 429 or ex.code == 20026:  # Maximum tries reached or no point in retrying
                                        l_errored_channels.append(l_error_text)
                                        break

                                except OSError as ex:
                                    TRACE(f"Error sending data to channel | Exception:{ex}",TRACE_LEVELS.ERROR)
                                    break
                                
                        l_trace += self._generate_log(l_text_to_send, l_embed_to_send, [x.filename for x in l_files_to_send], l_succeded_channels, l_errored_channels)     # Generate trace of sent file
            # Save into file
            if self.generate_log and l_trace:
                with suppress(FileExistsError):
                    os.mkdir(m_server_log_output_path)
                with open(os.path.join(m_server_log_output_path, self.guild_file_name),'a', encoding='utf-8') as l_logfile:
                    l_logfile.write(l_trace)

#######################################################################
# Functions
#######################################################################
def run(token : str,
        server_list : List[GUILD],
        is_user : bool =False,
        user_callback : bool=None,
        server_log_output : str ="Logging",
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

    m_user_callback = user_callback                 ## Called after framework has started
    m_server_log_output_path = server_log_output    ## Path to folder where to crete server logs
    m_server_list = server_list                     ## List of guild objects to iterate thru in the advertiser task
    m_debug = debug                                 ## Print trace messages to the console for debugging purposes
    m_client = DISCORD_CLIENT()                     ## Create a Client object for communication with discord's API

    if is_user:
        TRACE("Bot is an user account which is against discord's ToS",TRACE_LEVELS.WARNING)
    m_client.run(token, bot=not is_user)


if __name__ == "__main__":
    raise Exception("This file is meant as a module, not to run directly! Import it in a sperate py file and call framework.run(user_call_back)")
