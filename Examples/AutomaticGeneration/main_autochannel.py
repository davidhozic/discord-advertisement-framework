
"""
Automatically generated file for Discord Advertisement Framework 4.0.0.
This can be run eg. 24/7 on a server without graphical interface.

The file has the required classes and functions imported, then the logger is defined and the
accounts list is defined.

At the bottom of the file the framework is then started with the run function.
"""

# Import the necessary items
from daf.logging.logger_json import LoggerJSON

from daf.messagedata.textdata import TextMessageData
from daf.message.text_based import TextMESSAGE
from daf.client import ACCOUNT
from daf.messagedata import FILE
from daf.message.messageperiod import FixedDurationPeriod
from datetime import timedelta
from daf.guild.guilduser import GUILD
from daf.message.base import AutoCHANNEL
from daf.logging.tracing import TraceLEVELS
import daf

# Define the logger
logger = LoggerJSON(
    path="C:\\Users\\david\\daf\\History",
)

# Define remote control context


# Defined accounts
accounts = [
    ACCOUNT(
        token="TOKEN_HERE",
        is_user=True,
        servers=[
            GUILD(
                snowflake=24141241241231,
                messages=[
                    TextMESSAGE(
                        data=TextMessageData(
                            content="[LIMITED TIME ONLY] The greatest ever NFT created! Buy today.",
                            files=[
                                FILE(filename="C:/Users/david/OneDrive/Slike/Screenshots/nft_preview.png"),
                            ],
                        ),
                        channels=AutoCHANNEL(
                            include_pattern="shill|promo",
                            exclude_pattern="projects",
                        ),
                        period=FixedDurationPeriod(
                            duration=timedelta(
                                minutes=30.0,
                            ),
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
    save_to_file=False
)
