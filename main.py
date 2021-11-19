import discord, time, asyncio, random
from discord.ext import commands

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
                       
        this.text = text
        this.timer = TIMER()


class GUILD:
    def __init__(this, guildid, channels_to_send_in, messages_to_send):
        this.guild =    guildid
        this.messages = messages_to_send
        this.channels = channels_to_send_in

    def initialize(this):
        this.guild = m_bot.get_guild(this.guild)
        this.channels = [this.guild.get_channel(x) for x in this.channels]
        
    async def advertise_force(this):
        for l_msg in this.messages:
            for l_channel in this.channels:
                #TRACE(f'Sending msg: "{l_msg.text}" into channel: {l_channel.name}')
                await l_channel.send(l_msg.text)

    async def advertise(this):
        for l_msg in this.messages:
            if  l_msg.timer.start() and l_msg.timer.elapsed() > l_msg.period:
                if l_msg.randomized_time == True:
                    l_msg.period = random.randrange(*l_msg.random_range)
                l_msg.timer.reset()
                for l_channel in this.channels:
                    #TRACE(f'Sending msg: "{l_msg.text}" into channel: {l_channel.name}')
                    await l_channel.send(l_msg.text)


# CONSTANTS
C_BOT_API_KEY = "OTA5MDYwMTIwNjIzODQxMzAy.YZVSvA.2QDp_iJcVXPQ_9LqUsvI4ZPwWmw"
C_DEBUG = True
C_IS_USER = True


## Hour constants
C_HOUR_TO_SECOND= 3600
C_MINUTE_TO_SECOND = 60

# Globals
m_bot = discord.Client()#commands.Bot("::", description="Commands")


C_MESSAGE = \
"""😈 🅰️🇩🅰️  🇺 🇳 🇩 🇪 🇷 🇼 🇴 🇷 🇱 🇩  😈 

               - a new upcoming project!

                 {INSERT YOUR INVITE LINK HERE}

                     ONLY 500 WHITELIST SPOTS

      ADA Underworld is releasing their Set 1 - Devils!

The release of 750 unique, hand-drawn, randomly generated
    NFTs on the Cardano blockchain coming early 2022!

Come join the server for many giveaways, whitelist,
                 awsome community and much more!


Come check it out!

Join our discord!
Check our Twitter: https://twitter.com/ada_underworld
https://cdn.discordapp.com/attachments/898701888676069386/910593996949168158/Underworld_shill_gif.gif"""



server_MetaVoicers = GUILD(
                890131961992081439,                          # ID Serverja
                [                                            # ID Channels
                    893592192147398666            
                ],
                # Messages
                [   #       secs                    text
                    MESSAGE(5*C_MINUTE_TO_SECOND, 10*C_MINUTE_TO_SECOND , "TEST")
                  # MESSAGE(0, 10*C_MINUTE_TO_SECOND, "TEST")  # Ce je prvi parameter 0, potem je cas vedno drugi parameter drugace pa sta prva dva parametra meje za nakljucno izbiro
                ]
                )

m_servers = [server_MetaVoicers]     # Vsi serverji

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
    for l_server in m_servers:
        l_server.initialize()
        await l_server.advertise_force()
    while True:
        await asyncio.sleep(1)
        for l_server in m_servers:
            await l_server.advertise()

def main():
    #m_bot.login(C_BOT_API_KEY)
    m_bot.run(C_BOT_API_KEY, bot=not C_IS_USER)
if __name__ == "__main__":
    main()
