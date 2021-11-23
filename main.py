from asyncio.tasks import gather
import discord, time, asyncio, random
from discord.ext import commands


# CONSTANTS
C_BOT_API_KEY = "OTExMzI2MjAwOTQ3OTMzMjI1.YZfwqQ.dHrpwrb1aQ_-WvJq7Apdaej9dLI"
C_DEBUG = True
C_IS_USER = False
C_MESSAGE = """Pridruzite se nam na Arduino delavnicah !"""


## Hour constants
C_HOUR_TO_SECOND= 3600
C_MINUTE_TO_SECOND = 60


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
    def __init__(this, start_period : float, end_period : float, text : str, channels : list):
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

    def initialize(this):       # Get objects from ids
        this.guild = GUILD.bot_object.get_guild(this.guild) # Transofrm guild id into API guild object
        if this.guild != None:
            for l_msg in this.messages:
                l_msg.channels = [GUILD.bot_object.get_channel(x) for x in l_msg.channels]  # Transform ids into API channel objects
            this.guild_file_name = this.guild.name.replace("/","_").replace("\\","_").replace(":","_").replace("!","_").replace("|","_").replace("*","_").replace("?","_").replace("<","_").replace(">", "_") + ".txt"

    async def advertise(this, force=False):
        l_trace = ""
        if this.guild != None:
            for l_msg in this.messages:
                if force or (l_msg.timer.start() and l_msg.timer.elapsed() > l_msg.period):
                    if l_msg.randomized_time == True:           # If first parameter to msg object is != 0
                            l_msg.period = random.randrange(*l_msg.random_range)
                    l_msg.timer.reset()
                    l_msg.timer.start()
                    
                    
                    for l_channel in l_msg.channels:
                        await l_channel.send(l_msg.text)
                    l_msg.generate_timestamp()
                    l_trace += f'Sending Message: "{l_msg.text}"\n\nServer: {this.guild.name}\nChannels: {[x.name for x in l_msg.channels]} \nTimestamp: {l_msg.last_timestamp}\n\n----------------------------------\n\n'
                    TRACE(l_trace)
        return l_trace if l_trace != "" else None
        


############################################################################################
#                               GUILD MESSAGES DEFINITION                                  #
############################################################################################

GUILD.server_list = [
GUILD(
        863071397207212052,                          # ID Serverja
        # Messages
        [   #       min-sec                     max-sec      sporocilo   #IDji kanalov
            MESSAGE(0*C_HOUR_TO_SECOND, 3 , C_MESSAGE, [863071397207212056, 909499439377416243]),
            # MESSAGE(0, 10*C_MINUTE_TO_SECOND, "TEST")  # Ce je prvi parameter 0, potem je cas vedno drugi parameter drugace pa sta prva dva parametra meje za nakljucno izbiro
        ]
    )
]


                                     
############################################################################################

# Debugging functions
def TRACE(message):
    if C_DEBUG:
        print(message)

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
        l_ret = await l_server.advertise(True)
        if l_ret != None:
            with open(f"{l_server.guild_file_name}",'a', encoding='utf-8') as l_logfile:
                l_logfile.write(l_ret)
    while True:
        await asyncio.sleep(1)
        for l_server in GUILD.server_list:
            l_ret = await l_server.advertise(False)
            if l_ret != None:
                with open(f"{l_server.guild_file_name}",'a', encoding='utf-8') as l_logfile:
                    l_logfile.write(l_ret)

def main():
    GUILD.bot_object.run(C_BOT_API_KEY, bot=not C_IS_USER)




if __name__ == "__main__":
    main()