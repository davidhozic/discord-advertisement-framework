
"""
Automatically generated file for Discord Advertisement Framework v2.6.0.
This can be run eg. 24/7 on a server without graphical interface.

The file has the required classes and functions imported, then the logger is defined and the
accounts list is defined.

At the bottom of the file the framework is then started with the run function.
"""

# Import the necessary items
from daf.logging._logging import LoggerJSON
from daf.logging.tracing import TraceLEVELS
from _discord.embeds import Embed
from daf.client import ACCOUNT
from datetime import timedelta
from datetime import datetime
from daf.guild import GUILD
from daf.message.base import AutoCHANNEL
from _discord.colour import Colour
from _discord.embeds import EmbedField
from daf.message.text_based import TextMESSAGE

import daf


# Define the logger
logger = LoggerJSON(path="./OutputPath/")

# Defined accounts
accounts = [
    ACCOUNT(
        token="DSNDASDJHSAKJDHASIKLJHDASKJLGDASJKHDFGAKSJHDFGKJAHSFDAKSJH",
        is_user=False,
        servers=[
            GUILD(
                snowflake=863071397207212052,
                messages=[
                    TextMESSAGE(
                        start_period=None,
                        end_period=timedelta(
                            seconds=10.0,
                        ),
                        data=Embed(
                            color=Colour(
                                value=16711680,
                            ),
                            title="Test Embed Title",
                            type="rich",
                            description="This is a test embedded message description.",
                            timestamp=datetime(
                                year=2023,
                                month=4,
                                day=2,
                            ),
                            fields=[
                                EmbedField(
                                    name="Field1",
                                    value="Value1",
                                ),
                            ],
                        ),
                        channels=AutoCHANNEL(
                            include_pattern="shill",
                            interval=timedelta(
                                seconds=5.0,
                            ),
                        ),
                        mode="send",
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
    debug=TraceLEVELS.NORMAL
)
