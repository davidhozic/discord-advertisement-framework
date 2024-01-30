
"""
Example shows the basic message shilling into a fixed DM.
A text message is sent every 8-12 hours (randomly chosen) and it contains a text content and 3 files.

!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
WARNING! Using this do directly shill to DM is VERY DANGEROUS!!!
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
There is no way to check for permissions with DM messages, thus the client
may try to make many forbidden requests. This will eventually result in Discord
banning. USE AT YOUR OWN RISK!!!!

If you just want to respond to DM messages, the DMResponder is a better example.
"""

# Import the necessary items
from daf.logging.logger_json import LoggerJSON

from daf.messagedata import FILE
from daf.messagedata.textdata import TextMessageData
from datetime import timedelta
from daf.client import ACCOUNT
from daf.message.text_based import DirectMESSAGE
from daf.message.messageperiod import RandomizedDurationPeriod
from daf.guild.guilduser import USER
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
        is_user=False,
        servers=[
            USER(
                snowflake=145196308985020416,
                messages=[
                    DirectMESSAGE(
                        data=TextMessageData(
                            content="Buy our red dragon NFTs today!",
                            files=[
                                FILE(filename="C:/Users/david/Downloads/Picture1.png"),
                                FILE(filename="H:/My Drive/PR/okroznice/2023/2023_01_28 - Skiing.md"),
                                FILE(filename="H:/My Drive/PR/okroznice/2023/2023_10_16 - Volitve SSFE.md"),
                            ],
                        ),
                        period=RandomizedDurationPeriod(
                            minimum=timedelta(hours=8.0),
                            maximum=timedelta(hours=12.0),
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
