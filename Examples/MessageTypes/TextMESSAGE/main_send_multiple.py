
"""
Example shows the basic message shilling into a fixed guild.
A text message is sent every 8-12 hours (randomly chosen) and it contains a text content and 3 files.
The message will be first sent in 4 hours.
"""

# Import the necessary items
from daf.logging.logger_json import LoggerJSON

from daf.messagedata import FILE
from daf.messagedata.textdata import TextMessageData
from datetime import timedelta
from daf.client import ACCOUNT
from daf.message.text_based import TextMESSAGE
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
                snowflake=123456789,
                messages=[
                    TextMESSAGE(
                        data=TextMessageData(
                            content="Buy our red dragon NFTs today!",
                            files=[
                                FILE(filename="C:/Users/david/Downloads/Picture1.png"),
                                FILE(filename="H:/My Drive/PR/okroznice/2023/2023_01_28 - Skiing.md"),
                                FILE(filename="H:/My Drive/PR/okroznice/2023/2023_10_16 - Volitve SSFE.md"),
                            ],
                        ),
                        channels=[123123231232131231, 329312381290381208321, 3232320381208321],
                        period=RandomizedDurationPeriod(
                            minimum=timedelta(hours=8.0),
                            maximum=timedelta(hours=12.0),
                            next_send_time=timedelta(hours=4.0),
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
