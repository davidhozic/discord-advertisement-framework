import datetime, Config, framework
from framework import GUILD, MESSAGE



## Messages constants
C_MESSAGE = """
Arduino Delavnice - 27.11.2021:
Pridruzite se arduino delavnicam, ki bodo 27.11.2021 ob 17.00 uri <@133674038546530305>
Preostali cas: {time_left}"""

def get_msg():
    l_time_left=(datetime.datetime(2021,11,27,17,15) - datetime.datetime.now()).total_seconds()
    if l_time_left <= 1*Config.C_MINUTE_TO_SECOND:
        l_time_left = "Manj kot minuta"
    elif l_time_left <= 1*Config.C_HOUR_TO_SECOND:
        l_time_left = "{:.2f}".format(l_time_left/Config.C_MINUTE_TO_SECOND)  + " min"
    elif l_time_left <= 1*Config.C_DAY_TO_SECOND:
        l_time_left = "{:.2f}".format(l_time_left/Config.C_HOUR_TO_SECOND) + "h"
    else:
        l_time_left = "{:.2f}".format(l_time_left/Config.C_DAY_TO_SECOND) + "d"
            
    return C_MESSAGE.format(time_left=l_time_left)



############################################################################################
#                               GUILD MESSAGES DEFINITION                                  #
############################################################################################

GUILD.server_list = [
GUILD(
        863071397207212052,                          # ID Serverja
        # Messages
        [   #       min-sec                     max-sec      sporocilo   #IDji kanalov
            MESSAGE(start_period=0, end_period=3 , text=get_msg, channels=[863071397207212056, 909499439377416243], clear_previous=False)
            # MESSAGE(0, 10*C_MINUTE_TO_SECOND, "TEST")  # Ce je prvi parameter 0, potem je cas vedno drugi parameter drugace pa sta prva dva parametra meje za nakljucno izbiro
        ]
    )
]
                                     
############################################################################################

framework.run()