import Config, discord, time, asyncio, random, datetime, math


# Debugging functions
def TRACE(message):
    if Config.C_DEBUG:
        print(message)

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


class MESSAGE:
    def __init__(this, start_period : float, end_period : float, text : str, channels : list, clear_previous : bool):
        if start_period == 0: 
            this.randomized_time = False
            this.period = end_period 
        else:
            this.randomized_time = True
            this.random_range = (start_period, end_period)
            this.period = random.randrange(*this.random_range)

        this.last_timestamp = None
        this.text = text
        this.channels = channels
        this.timer = TIMER()
        this.clear_previous = clear_previous
        this.sent_msg_objs = []
    def generate_timestamp(this):
        l_timestruct = time.localtime()
        this.last_timestamp = "Date:{:02d}.{:02d}.{:04d} Time:{:02d}:{:02d}"
        this.last_timestamp = this.last_timestamp.format(l_timestruct.tm_mday, l_timestruct.tm_mon, l_timestruct.tm_year,l_timestruct.tm_hour,l_timestruct.tm_min)


class GUILD:
    server_list = []
    bot_object = discord.Client()

    def __init__(this, guildid,  messages_to_send):
        this.guild =    guildid
        this.messages = messages_to_send
        this.guild_file_name = None
        this.first_advert = None
    def initialize(this):       # Get objects from ids
        this.first_advert = True
        this.guild = GUILD.bot_object.get_guild(this.guild) # Transofrm guild id into API guild object
        if this.guild != None:
            for l_msg in this.messages:
                l_msg.channels = [GUILD.bot_object.get_channel(x) for x in l_msg.channels]  # Transform ids into API channel objects
            this.guild_file_name = this.guild.name.replace("/","-").replace("\\","-").replace(":","-").replace("!","-").replace("|","-").replace("*","-").replace("?","-").replace("<","(").replace(">", ")") + ".txt"

    async def advertise(this):
        l_trace = ""
        if this.guild != None:
            for l_msg in this.messages:
                if this.first_advert or (l_msg.timer.start() and l_msg.timer.elapsed() > l_msg.period):
                    l_msg.timer.reset()
                    l_msg.timer.start()
                    this.first_advert = False
                    if l_msg.randomized_time == True:           # If first parameter to msg object is != 0
                            l_msg.period = random.randrange(*l_msg.random_range)
                       
                    # Clear previous msgs
                    if l_msg.clear_previous:
                        for l_sent_msg_obj in l_msg.sent_msg_objs:
                            await l_sent_msg_obj.delete()
                        l_msg.sent_msg_objs.clear()

                    # Send messages    
                    l_text_to_send = l_msg.text() if callable(l_msg.text) else l_msg.text
                    for l_channel in l_msg.channels:
                            l_msg.sent_msg_objs.append(await l_channel.send(l_text_to_send))
                    l_msg.generate_timestamp()
                    l_trace += f'Sending Message: "{l_text_to_send}"\n\nServer: {this.guild.name}\nChannels: {[x.name for x in l_msg.channels]} \nTimestamp: {l_msg.last_timestamp}\n\n----------------------------------\n\n'
                    TRACE(l_trace)
        # Return for file write
        return l_trace if l_trace != "" else None
        
# Event functions
@GUILD.bot_object.event
async def on_ready():
    TRACE(f"Logged in as {GUILD.bot_object.user}")
    l_advertiser = asyncio.create_task(advertiser())
    asyncio.gather(l_advertiser)

# Advertising task
async def advertiser(): 
    for l_server in GUILD.server_list:
        l_server.initialize()

    while True:
        await asyncio.sleep(0.5)
        for l_server in GUILD.server_list:
            l_ret = await l_server.advertise()
            if l_ret is not None and Config.C_FILE_OUTPUT:
                with open(f"{l_server.guild_file_name}",'a', encoding='utf-8') as l_logfile:
                    l_logfile.write(l_ret)


def run():
    GUILD.bot_object.run(Config.C_BOT_API_KEY, bot=not Config.C_IS_USER)