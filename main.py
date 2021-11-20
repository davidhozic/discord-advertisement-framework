import discord, time, asyncio, random
from discord.ext import commands


# CONSTANTS
C_BOT_API_KEY = "OTA5MDYwMTIwNjIzODQxMzAy.YZVSvA.2QDp_iJcVXPQ_9LqUsvI4ZPwWmw"
C_DEBUG = True
C_IS_USER = True
C_LOG_FILE_NAME = "log.txt"
C_MESSAGE = '😈 🅰️🇩🅰️  🇺 🇳 🇩 🇪 🇷 🇼 🇴 🇷 🇱 🇩  😈 \n\n               - a new upcoming project!\n\n                 {INSERT YOUR INVITE LINK HERE}\n\n                     ONLY 500 WHITELIST SPOTS\n\n      ADA Underworld is releasing their Set 1 - Devils!\n\nThe release of 750 unique, hand-drawn, randomly generated\n    NFTs on the Cardano blockchain coming early 2022!\n\nCome join the server for many giveaways, whitelist,\n                 awsome community and much more!\n\n\nCome check it out!\n\nJoin our discord!\nCheck our Twitter: https://twitter.com/ada_underworld\nhttps://cdn.discordapp.com/attachments/898701888676069386/910593996949168158/Underworld_shill_gif.gif'


## Hour constants
C_HOUR_TO_SECOND= 3600
C_MINUTE_TO_SECOND = 60

# Globals
m_bot = discord.Client()#commands.Bot("::", description="Commands")



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
    def __init__(this, start_period : float, end_period : float, text : str):
        if start_period == 0: 
            this.randomized_time = False
            this.period = end_period 
        else:
            this.randomized_time = True
            this.random_range = (start_period, end_period)
            this.period = random.randrange(*this.random_range)

        this.last_timestamp = None
        this.text = text
        this.timer = TIMER()
    def generate_timestamp(this):
        l_timestruct = time.localtime()
        this.last_timestamp = "Date:{:02d}.{:02d}.{:04d} Time:{:02d}:{:02d}"
        this.last_timestamp = this.last_timestamp.format(l_timestruct.tm_mday, l_timestruct.tm_mon, l_timestruct.tm_year,l_timestruct.tm_hour,l_timestruct.tm_min)


class GUILD:
    server_list = []

    def __init__(this, guildid, channels_to_send_in, messages_to_send):
        this.guild =    guildid
        this.messages = messages_to_send
        this.channels = channels_to_send_in
        this.guild_name = None
    def initialize(this):       # Get objects from ids
        this.guild = m_bot.get_guild(this.guild)
        this.channels = [this.guild.get_channel(x) for x in this.channels]
        this.guild_name = this.guild.name

    async def advertise(this, force=False):
        l_trace = ""
        for l_msg in this.messages:
            if force or (l_msg.timer.start() and l_msg.timer.elapsed() > l_msg.period):
                if l_msg.randomized_time == True:           # If first parameter to msg object is != 0
                        l_msg.period = random.randrange(*l_msg.random_range)
                l_msg.timer.reset()
                l_msg.timer.start()
                l_msg.generate_timestamp()
                l_trace += f'Sending Message: "{l_msg.text}"\n\nServer: {this.guild_name}\nChannels: {[x.name for x in this.channels]} \nTimestamp: {l_msg.last_timestamp}\n\n----------------------------------\n\n'
                TRACE(l_trace)
                for l_channel in this.channels:
                    await l_channel.send(l_msg.text)
                    time.sleep(4)
                    
        return l_trace
        


############################################################################################
#                               GUILD MESSAGES DEFINITION                                  #
############################################################################################


server_Solnanas = GUILD(   # ID Serverja
                        890131961992081439,   
                        # Tabela Kanalov                       
                        [   
                            893592192147398666            
                        ],
                        # Tabela sporocil
                        [   #       minimum-sec                     maximum-sec           sporocilo
                            MESSAGE(360 * C_MINUTE_TO_SECOND, 420 * C_MINUTE_TO_SECOND , C_MESSAGE)
                            # MESSAGE(0, 10*C_MINUTE_TO_SECOND, "TEST")  # Ce je prvi parameter 0, potem je cas vedno drugi parameter drugace pa sta prva dva parametra meje za nakljucno izbiro
                        ]
)

GUILD.server_list = [server_Solnanas]
############################################################################################

# Debugging functions
def TRACE(message):
    if C_DEBUG:
        print(message)

# Event functions
@m_bot.event
async def on_ready():
    TRACE(f"Logged in as {m_bot.user}")
    l_advertiser = asyncio.create_task(advertiser())
    asyncio.gather(l_advertiser)

# Advertising task
async def advertiser(): 
    for l_server in GUILD.server_list:
        l_server.initialize()
        l_ret = await l_server.advertise(True)
        if l_ret != None:
            with open(f"{l_server.guild_name}_{C_LOG_FILE_NAME}",'a', encoding='utf-8') as l_logfile:
                l_logfile.write(l_ret)
    while True:
        await asyncio.sleep(1)
        for l_server in GUILD.server_list:
            l_ret = await l_server.advertise(False)
            if l_ret != None:
                with open(f"{l_server.guild_name}_{C_LOG_FILE_NAME}",'a', encoding='utf-8') as l_logfile:
                    l_logfile.write(l_ret)

def main():
    m_bot.run(C_BOT_API_KEY, bot=not C_IS_USER)

if __name__ == "__main__":
    main()



