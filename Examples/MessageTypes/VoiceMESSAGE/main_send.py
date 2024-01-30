
"""
Example shows the basic message shilling into a fixed guild.
A text message is sent every 30-90 minutes (randomly chosen) and it plays a single audio file.
The message will be first sent in 10 minutes.
"""

# Import the necessary items
from daf.logging.logger_json import LoggerJSON

from daf.messagedata import FILE
from daf.messagedata.voicedata import VoiceMessageData
from datetime import timedelta
from daf.client import ACCOUNT
from daf.message.voice_based import VoiceMESSAGE
from daf.message.messageperiod import RandomizedDurationPeriod
from daf.guild.guilduser import GUILD
from daf.logging.tracing import TraceLEVELS
import daf

# Define the logger
logger = LoggerJSON(
    path="C:\\Users\\david\\daf\\History",
)

# Defined accounts
accounts = [
    ACCOUNT(
        token="TOKEN",
        is_user=True,
        servers=[
            GUILD(
                snowflake=318732816317823168276278,
                messages=[
                    VoiceMESSAGE(
                        data=VoiceMessageData(FILE(filename="./VoiceMESSAGE.mp3")),
                        channels=[1136787403588255784, 1199125280149733449],
                        period=RandomizedDurationPeriod(
                            minimum=timedelta(minutes=30),
                            maximum=timedelta(minutes=90),
                            next_send_time=timedelta(minutes=10),
                        ),
                    ),
                ],
                logging=True,
            ),
        ],
    ),
]

# Run the framework (blocking)
daf.run(
    accounts=accounts,
    logger=logger,
    debug=TraceLEVELS.NORMAL,
)
