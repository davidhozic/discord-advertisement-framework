
"""
Example shows the basic message shilling into a fixed guild.
A text message is sent every 30-90 minutes (randomly chosen) and it plays a single audio file.
The message will be first sent in 10 minutes.

The message audio is dynamically obtained through the get_data method of MyDynamicData.
The custom data class must inherit the DynamicVoiceMessageData class.
"""

# Import the necessary items
from daf.logging.logger_json import LoggerJSON

from daf.messagedata import FILE
from daf.messagedata.voicedata import VoiceMessageData
from daf.messagedata.dynamicdata import DynamicMessageData
from datetime import timedelta
from daf.client import ACCOUNT
from daf.message.voice_based import VoiceMESSAGE
from daf.message.messageperiod import RandomizedDurationPeriod
from daf.guild.guilduser import GUILD
from daf.logging.tracing import TraceLEVELS
import daf

import os
os.chdir(os.path.dirname(__file__))

# Define the logger
logger = LoggerJSON(
    path="./Logs/",
)


class MyDynamicData(DynamicMessageData):
    def __init__(self, path: str) -> None:
        self.path = path
        self.last_index = 0

    def get_data(self):
        """
        Cycles through the list of self.data.
        """
        files = [filename for filename in os.listdir("./") if filename.endswith(".mp3")]
        if not files:
            return None

        self.last_index = (self.last_index + 1) % len(files)

        filename = files[self.last_index]
        return VoiceMessageData(FILE(filename))


# Defined accounts
accounts = [
    ACCOUNT(
        token="TOKEN",
        is_user=True,
        servers=[
            GUILD(
                snowflake=8371298361287361287,
                messages=[
                    VoiceMESSAGE(
                        data=MyDynamicData("./"),
                        channels=[41251423123211412, 3123812093812093223],
                        period=RandomizedDurationPeriod(
                            minimum=timedelta(seconds=60),
                            maximum=timedelta(seconds=90),
                            # next_send_time=timedelta(minutes=10),
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
