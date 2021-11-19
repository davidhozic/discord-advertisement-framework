import discord, time, asyncio


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
    def __init__(this, period : float, text : str):
        this.period = period
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
        

    async def advertise(this):
        for l_msg in this.messages:
            if  l_msg.timer.start() and l_msg.timer.elapsed() > l_msg.period:
                l_msg.timer.reset()
                for l_channel in this.channels:
                    await l_channel.send(l_msg.text)





# CONSTANTS
C_BOT_API_KEY = "OTExMzI2MjAwOTQ3OTMzMjI1.YZfwqQ.dHrpwrb1aQ_-WvJq7Apdaej9dLI"
C_DEBUG = True

## Hour constants
C_HOUR_TO_SECOND= 3600
C_MINUTE_TO_SECOND = 60

# Globals
m_bot = discord.Client()

m_server1 = GUILD(863071397207212052,               # ID Serverja
                # ID Channels
                [
                    863071397207212056,# General
                ],
                # Messages
                [   #       secs  text
                    MESSAGE(1*C_MINUTE_TO_SECOND , "<@133674038546530305>"),
                ]
                )


m_servers = [m_server1]     # Vsi serverji


# Debugging functions
def TRACE(message):
    if C_DEBUG:
        print(message)


@m_bot.event
async def on_ready():
    TRACE(f"We have logged in as {m_bot.user}")
    l_advertiser = asyncio.create_task(advertiser())
    asyncio.gather(l_advertiser)

async def advertiser(): 
    for l_server in m_servers:
        l_server.initialize()
    while True:
        await asyncio.sleep(0.001)
        for l_server in m_servers:
            await l_server.advertise()


def main():
    m_bot.run(C_BOT_API_KEY)

if __name__ == "__main__":
    main()

