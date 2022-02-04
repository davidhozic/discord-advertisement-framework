import Config, discord, time, asyncio, random, types, os
from typing import  Union
from debug import *



# Contants
## Hour constants
C_DAY_TO_SECOND = 86400
C_HOUR_TO_SECOND= 3600
C_MINUTE_TO_SECOND = 60

# Globals
m_user_callback = None  # User provided function to call after framework is ready

# Decortors
## Decorator classes


class __function_cls_base__:
    """
    type:   Dummy class
    @info:  Only used by framework to check if the data parameter of framework.MESSAGE is a framework.FUNCTION object -- isinstance returns True if the class parameter is either the class that created it or a base clase of that class (or base of the base  class, etc..)
    """
    pass

def FUNCTION(fnc):
    """
    type:   Decorator
    name:   FUNCTION
    info:   Decorator used to create a class that will create a callable framework function object
    return: __FUNCTION_CLS__
    usage:  \n\n@framework.FUNCTION\ndef function(a,b,c)\n\treturn [str | embed | file | list | tuple]
    """
    class __FUNCTION_CLS__(__function_cls_base__):
        def __init__(this, *args, **kwargs):
            this.fnc = fnc
            this.args, this.kwargs = args, kwargs 
        def __call__(this):
            return this.fnc(*this.args, **this.kwargs)
    return __FUNCTION_CLS__

# Classes
class TIMER:
    def __init__(this):
        this.running = False
        this.min = 0
    def start(this):
        if this.running:
            return True
        this.running = True
        this.ms = time.time()
        return False
    def elapsed(this):
        return time.time() - this.ms if this.running else 0
    def reset (this):
        this.running = False

class EMBED_FIELD:
    """
    Embedded field class for use in EMBED object constructor
    Parameters:
    -  Name         : str    -- Name of the field 
    -  Content      : str    -- Content of the embedded field
    -  Inline       : bool   -- Make this field appear in the same line as the previous field
    """
    def __init__(this, name : str, content : str, inline : bool=False):
        this.name = name
        this.content = content 
        this.inline = inline

    def __iter__(this):
        class EMBED_FIELD_ITER:
            def __init__(this, data):
                this.__data = data
                this.__index = 0
                this.__max = len(data)
            def __next__(this):
                if this.__index == this.__max:
                    raise StopIteration
                this.__index +=1
                return this.__data[this.__index-1]
        return EMBED_FIELD_ITER([this.name, this.content,this.inline])
  
       
        
class EMBED(discord.Embed):
    """
    Derrived class of discord.Embed with easier definition
        Parameters: 
            - author_name       : str   -- Name of embed author
            - author_image_url  : str   -- Url to author image
            - image             : str   -- Url of image to be placed at the end of the embed
            - thumbnail         : str   -- Url of image that will be placed at the top right of embed
            - fields            : list  -- List of EMBED_FIELD objects
    """
    # Exceptions
    C_AUTHOR_EXCEPT = "Incorrect author parameters"
    class AuthorException(BaseException):
        pass
    C_FIELD_PARAM_EXCEPT  = "The fields parameter must be a list of class EMBED_FIELD"
    C_FIELD_LEN_EXCEPT    = "The field content can be only up to 1023 per field"
    class FieldsException(BaseException):
        pass
    
    # Functions
    def __init__(this, *,author_name:str=None,author_image_url=discord.embeds.EmptyEmbed, image :str=None, thumbnail : str = None, fields : list):
        super().__init__()
        ## Set author
        ### Raise exception if incorrect parameters are passed
        if not isinstance(author_name, Union[str,discord.embeds._EmptyEmbed,None]) or not isinstance(author_image_url, Union[str,discord.embeds._EmptyEmbed]):
             raise EMBED.AuthorException(EMBED.C_AUTHOR_EXCEPT)
        if author_name:
            this.set_author(name=author_name, icon_url=author_image_url)

        ## Set image
        if image:
            this.set_image(url=image)

        ## Set thumbnail
        if thumbnail:
            this.set_thumbnail(url=thumbnail)
        
        ## Set fields
        ### Raise exception if incorrect parameters are passed
        if not isinstance(fields, list) or not len(fields) or not isinstance(fields[0], EMBED_FIELD):
            raise EMBED.FieldsException(EMBED.C_FIELD_PARAM_EXCEPT)
        ### Set fields
        for field_name, content, inline in fields:
            if len(content) > 1023:
                raise EMBED.FieldsException(EMBED.C_FIELD_LEN_EXCEPT) #### Maximum length is 1023
            this.add_field(name=field_name,value=content,inline=inline)
        




class FILE:
    def __init__(this, filename):
        this.filename = filename

class MESSAGE:
    def __init__(this, start_period : float, end_period : float, data : Union[str, discord.Embed, list, types.FunctionType, FILE], channel_ids : list, clear_previous : bool, start_now : bool):
        if start_period is None:            # If start_period is none -> period will not be randomized
            this.randomized_time = False
            this.period = end_period 
        else:                               
            this.randomized_time = True             
            this.random_range = (start_period, end_period)
            this.period = random.randrange(*this.random_range)  # This will happen after each sending as well

        this.data = data
        this.channels = channel_ids
        this.timer = TIMER()
        this.clear_previous = clear_previous
        this.force_retry = {"ENABLED" : start_now, "TIME" : 0}
        this.sent_msg_objs = []
   
class GUILD:
    server_list = []
    bot_object = discord.Client()

    def __init__(this, guild_id : int,  messages_to_send : list, generate_log : bool = False):
        this.guild =    guild_id
        this.messages = messages_to_send
        this.generate_log = generate_log
        this.guild_file_name = None
    async def initialize(this):       # Get objects from ids
        l_guild_id = this.guild
        this.guild = GUILD.bot_object.get_guild(l_guild_id) # Transofrm guild id into API guild object
        if this.guild != None:
            for l_msg in this.messages:
                if isinstance(l_msg, MESSAGE):
                    for x in range(len(l_msg.channels)):
                        l_msg.channels[x] = GUILD.bot_object.get_channel(l_msg.channels[x])
                    while None in l_msg.channels:
                        l_msg.channels.remove(None)
                else:
                    TRACE(f"Invalid data type argument passed to messages list in guild id {l_guild_id}\nPlease fix the error and restart application.\nEntering sleep forever...", level=TRACE_LEVELS.ERROR)
                    while l_msg in this.messages:
                        this.messages.remove(l_msg)
            this.guild_file_name = this.guild.name.replace("/","-").replace("\\","-").replace(":","-").replace("!","-").replace("|","-").replace("*","-").replace("?","-").replace("<","(").replace(">", ")") + ".md"
        else:
            TRACE(f"Unable to create server object from server id: {l_guild_id}", TRACE_LEVELS.ERROR)

    def _generate_log(this, sent_text : str, sent_embed : discord.Embed, sent_files : list, succeeded_ch : list, failed_ch : list):
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
    Server: {this.guild.name}
    Succeeded in channels: {succeeded_ch}
    Failed in channels: {failed_ch}
    Timestamp: {l_timestamp}
    ```
__________________________________________________________
'''

    async def advertise(this):
        l_trace = ""
        if this.guild != None:
            for l_msg in this.messages:
                if l_msg.timer.start() and (not l_msg.force_retry["ENABLED"] and l_msg.timer.elapsed() > l_msg.period or l_msg.force_retry["ENABLED"] and l_msg.timer.elapsed() > l_msg.force_retry["TIME"]) :  # If timer has started and timer is above set period/above force_retry period
                    l_msg.timer.reset()
                    l_msg.timer.start()
                    l_msg.force_retry["ENABLED"] = False
                    if l_msg.randomized_time == True:           # If first parameter to msg object is != None
                            l_msg.period = random.randrange(*l_msg.random_range)
                       
                    # Clear previous msgs
                    if l_msg.clear_previous:
                        for l_sent_msg_obj in l_msg.sent_msg_objs:
                            try:
                                await l_sent_msg_obj.delete()
                            except Exception as ex:
                                if ex.status == 429:
                                    await asyncio.sleep(int(ex.response.headers["Retry-After"])+1)
                                    
                        l_msg.sent_msg_objs.clear()

                    
                    # Parse data from the data parameter
                    l_data_to_send  = None     
                    if isinstance(l_msg.data, __function_cls_base__):    
                        l_data_to_send = l_msg.data()
                    else:
                        l_data_to_send = l_msg.data

                    l_embed_to_send = None
                    l_text_to_send  = None
                    l_files_to_send  = []
                    if isinstance(l_data_to_send, list) or isinstance(l_data_to_send, tuple):
                        # data is list -> parse each element
                        for element in l_data_to_send:
                            if isinstance(element, str):
                                l_text_to_send = element
                            elif isinstance(element, EMBED):
                                l_embed_to_send = element
                            elif isinstance(element, FILE):
                                l_files_to_send.append(element)
                    elif isinstance(l_data_to_send, EMBED):
                        l_embed_to_send = l_data_to_send
                    elif isinstance(l_data_to_send, str):
                        l_text_to_send = l_data_to_send
                    elif isinstance(l_data_to_send, FILE):
                        l_files_to_send.append(l_data_to_send)
                    
                    # Send messages                     
                    if l_text_to_send or l_embed_to_send or l_files_to_send:
                        l_errored_channels = []
                        l_succeded_channels= []

                        ## Open files
                        if l_files_to_send:
                            l_tmp = l_files_to_send
                            l_files_to_send = []
                            for l_fileobj in l_tmp:
                                try:
                                    l_files_to_send.append(open(l_fileobj.filename, "rb"))
                                except Exception as l_file_exception:  
                                    TRACE(f"FILE_EXCEPTION for file: {l_fileobj.filename} | Exception: {l_file_exception}", TRACE_LEVELS.ERROR) 
                        
                        # Send to channels
                        for l_channel in l_msg.channels:
                            try:
                                if l_channel.guild.id != this.guild.id:
                                    raise Exception(f"Channel is not in part of this guild ({this.guild.name}) but is part of a different guild ({l_channel.guild.name})")     

                                # SEND TO CHANNEL
                                l_discord_sent_msg = await l_channel.send(l_text_to_send, embed=l_embed_to_send, files=[discord.File(x) for x in l_files_to_send])

                                l_succeded_channels.append(l_channel.name)
                                if l_msg.clear_previous:
                                    l_msg.sent_msg_objs.append(l_discord_sent_msg)
                            except discord.HTTPException as ex:     
                                # Failed to send message
                                l_error_text = f"{l_channel.name} - Reason: {ex}"
                                if ex.status == 429:
                                    l_msg.force_retry["ENABLED"] = True 
                                    l_msg.force_retry["TIME"] = int(ex.response.headers["Retry-After"]+1)    # Slow Mode detected -> wait the remaining time
                                    if ex.code != 20026:    # Rate limit but not slow mode -> put the framework to sleep as it won't be able to send any messages globaly
                                        await asyncio.sleep(l_msg.force_retry["TIME"])  # Rate limit (global for account) -> wait!
                                    l_error_text += f" - Retrying after {l_msg.force_retry['TIME']} seconds"
                                l_errored_channels.append(l_error_text)
                            except OSError as ex:
                                TRACE(f"Error sending data to channels | Exception:{ex}",TRACE_LEVELS.ERROR)
                        ## Close files if it was opened
                        if l_files_to_send:
                            for l_file in l_files_to_send:
                                try:
                                    l_file.close()                             
                                except: # If file is already closed
                                    pass

                        l_trace += this._generate_log(l_text_to_send, l_embed_to_send, [x.name for x in l_files_to_send], l_succeded_channels, l_errored_channels)     # Generate trace of sent file
            # Save into file
            if this.generate_log and l_trace:
                if Config.C_SERVER_OUTPUT_FOLDER not in os.listdir("./"):
                    os.mkdir(Config.C_SERVER_OUTPUT_FOLDER)
                with open(os.path.join(Config.C_SERVER_OUTPUT_FOLDER, this.guild_file_name),'a', encoding='utf-8') as l_logfile:
                    l_logfile.write(l_trace)
        
# Event functions
@GUILD.bot_object.event
async def on_ready():
    TRACE(f"Logged in as {GUILD.bot_object.user}", TRACE_LEVELS.NORMAL)
    asyncio.gather(asyncio.create_task(advertiser()))
    if m_user_callback: # If it's not none
        m_user_callback() # Call user provided function after framework has started
    

# Advertising task
async def advertiser(): 
    for l_server in GUILD.server_list:
        await l_server.initialize()

    while True:
        await asyncio.sleep(0.01)
        for l_server in GUILD.server_list:
            await l_server.advertise()
                

# Called after framework is ran
def run(user_callback=None):
    global m_user_callback
    m_user_callback = user_callback   # This function will be called once
    if Config.C_IS_USER:
        TRACE("Bot is an user account which is against discord's ToS",TRACE_LEVELS.WARNING)
    GUILD.bot_object.run(Config.C_BOT_API_KEY, bot=not Config.C_IS_USER)




if __name__ == "__main__":
    raise Exception("This file is meant as a module, not to run directly! Import it in a sperate py file and call framework.run(user_call_back)")