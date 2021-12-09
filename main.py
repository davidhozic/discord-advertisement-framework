import asyncio
import  framework, Config
from framework import GUILD, MESSAGE

import FE_UNI.arduino
import FE_UNI.uni
    

############################################################################################
#                               GUILD MESSAGES DEFINITION                                  #
############################################################################################

GUILD.server_list = [
GUILD(
        863071397207212052,                          # ID Serverja
        # Messages
        [   #       min-sec                     max-sec      sporocilo   #IDji kanalov
            MESSAGE(start_period=0, end_period=1 , text=FE_UNI.uni.FE_UNI_OBVESTILA.get_msg, channels=[863071397207212056], clear_previous=False, start_now=True),
            MESSAGE(start_period=0, end_period=1*Config.C_DAY_TO_SECOND , text=FE_UNI.arduino.get_msg, channels=[863071397207212056], clear_previous=True, start_now=True)
        ]
    )
]
                                     
############################################################################################

def main():
    asyncio.gather(asyncio.create_task(FE_UNI.uni.FE_UNI_OBVESTILA.file_processor()))

if __name__ == "__main__":
    framework.run(user_callback=main)
    