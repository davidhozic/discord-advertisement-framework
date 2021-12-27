from typing import Union, Optional
import Config, discord, time, asyncio, random
from debug import *
import types



# Contants
## Hour constants
C_DAY_TO_SECOND = 86400
C_HOUR_TO_SECOND= 3600
C_MINUTE_TO_SECOND = 60

# Globals
m_user_callback = None  # User provided function to call after framework is ready
m_advertiser_task : asyncio.Task = None

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
        this.force = start_now
        this.sent_msg_objs = []
   
class GUILD:
    server_list = []
    bot_object = discord.Client()

    def __init__(this, guild_id : int,  messages_to_send : list, generate_log : Optional[bool] = True):
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

    def _generate_log(this, sent_text : str, sent_embed : discord.Embed, succeeded_ch : list, failed_ch : list):
        l_tmp = ""
        if sent_text:
            for line in sent_text.split("\n"):
                l_tmp += f"\t{line}\n"
        sent_text = l_tmp.rstrip()
        l_tmp = ""
        if sent_embed:
            for field in sent_embed.fields:
                l_tmp += f"\n- {field.name}\n\t```\n"

                for line in field.value.split("\n"):
                    l_tmp+=f"\t{line}\n"
                l_tmp = l_tmp.rstrip()
                l_tmp += "\n\t```"
        sent_embed = l_tmp
        l_timestruct = time.localtime()
        l_timestamp = "Date:{:02d}.{:02d}.{:04d} Time:{:02d}:{:02d}".format(l_timestruct.tm_mday, l_timestruct.tm_mon, l_timestruct.tm_year,l_timestruct.tm_hour,l_timestruct.tm_min)
        return f'''                         
# MESSAGE LOG:
## Text:
-   ```  	
{sent_text}
    ```
## Embed fields:
{sent_embed}

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
                if l_msg.force or (l_msg.timer.start() and l_msg.timer.elapsed() > l_msg.period):
                    l_msg.timer.reset()
                    l_msg.timer.start()
                    l_msg.force = False
                    if l_msg.randomized_time == True:           # If first parameter to msg object is != 0
                            l_msg.period = random.randrange(*l_msg.random_range)
                       
                    # Clear previous msgs
                    if l_msg.clear_previous:
                        for l_sent_msg_obj in l_msg.sent_msg_objs:
                            await l_sent_msg_obj.delete()
                        l_msg.sent_msg_objs.clear()


                    # Check if function was passed or function tuple
                    l_data_to_send  = None     
                    if callable(l_msg.data):    # Function without parameters
                        try:
                            l_data_to_send = l_msg.data()
                        except Exception as ex:
                            TRACE(f"Error calling the function: Exception : {ex}", TRACE_LEVELS.ERROR)
                    elif (isinstance(l_msg.data, tuple) or isinstance(l_msg.data, list)) and callable(l_msg.data[0]): # array of function with it's parameters
                        try:
                            l_data_to_send = l_msg.data[0](*l_msg.data[1:]) # First element is function, the rest are it's parameters
                        except Exception as ex:
                            TRACE(f"Error calling the function: Exception : {ex}", TRACE_LEVELS.ERROR)
                    else:
                        l_data_to_send = l_msg.data


                    l_embed_to_send = None
                    l_text_to_send  = None
                    l_files_to_send  = []
                    # Check data type of data
                    if isinstance(l_data_to_send, list) or isinstance(l_data_to_send, tuple):
                        for element in l_data_to_send:
                            if isinstance(element, str):
                                l_text_to_send = element
                            elif isinstance(element, discord.Embed):
                                l_embed_to_send = element
                            elif isinstance(element, FILE):
                                l_files_to_send.append(element)
                    elif isinstance(l_data_to_send, discord.Embed):
                        l_embed_to_send = l_data_to_send
                    elif isinstance(l_data_to_send, str):
                        l_text_to_send = l_data_to_send
                    elif isinstance(l_data_to_send, FILE):
                        l_files_to_send.append(l_data_to_send)
                    
                    # Send messages                     
                    if l_text_to_send or l_embed_to_send or l_files_to_send:
                        l_errored_channels = []
                        l_succeded_channels= []
                        for l_channel in l_msg.channels:
                            try:
                                if l_channel.guild.id != this.guild.id:
                                    raise Exception(f"Channel is not in part of this guild ({this.guild.name}) but is part of a different guild ({l_channel.guild.name})")
                                                                
                                ## Open files if it's not none
                                if l_files_to_send.__len__() > 0:
                                    l_files_to_send = [  discord.File(open(x.filename)) for x in l_files_to_send]
                                
                                ## Send message to discord
                                l_discord_sent_msg = await l_channel.send(l_text_to_send, embed=l_embed_to_send, files=l_files_to_send)
                                
                                ## Close files if it was opened
                                if l_files_to_send.__len__() > 0:
                                    for l_file in l_files_to_send:
                                        l_file.close()

                                l_succeded_channels.append(l_channel.name)
                                if l_msg.clear_previous:
                                    l_msg.sent_msg_objs.append(l_discord_sent_msg)
                            except Exception as ex:
                                l_errored_channels.append(f"{l_channel.name} - Reason: {ex}")
                        
                        l_embed_log = ""
                        if l_embed_to_send:
                            for l_embed_msg in l_embed_to_send.fields:
                                l_embed_log += f"\tField name: {l_embed_msg.name}\n\tField data: {l_embed_msg.value}\n----------------------------------\n"
                        if l_embed_log == "":
                            l_embed_log = None
                        l_trace += this._generate_log(l_text_to_send, l_embed_to_send, l_succeded_channels, l_errored_channels)
                        TRACE(l_trace, TRACE_LEVELS.NORMAL)
        # Return for file write
        return l_trace if l_trace != "" else None
        
# Event functions
@GUILD.bot_object.event
async def on_ready():
    global m_advertiser_task
    TRACE(f"Logged in as {GUILD.bot_object.user}", TRACE_LEVELS.NORMAL)
    m_advertiser_task = asyncio.create_task(advertiser())
    asyncio.gather(m_advertiser_task)
    if m_user_callback: # If it's not none
        m_user_callback() # Call user provided function after framework has started
    

# Advertising task
async def advertiser(): 
    global m_advertiser_task
    for l_server in GUILD.server_list:
        await l_server.initialize()

    while True:
        await asyncio.sleep(0.01)
        for l_server in GUILD.server_list:
            l_ret = await l_server.advertise()
            if l_ret is not None and l_server.generate_log:
                with open(f"{l_server.guild_file_name}",'a', encoding='utf-8') as l_logfile:
                    l_logfile.write(l_ret)

def run(user_callback=None):
    global m_user_callback
    m_user_callback = user_callback   # This function will be called once
    if Config.C_IS_USER:
        TRACE("Bot is an user account which is against discord's ToS",TRACE_LEVELS.WARNING)
    GUILD.bot_object.run(Config.C_BOT_API_KEY, bot=not Config.C_IS_USER)
