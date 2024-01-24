
"""
Example shows the basic message shilling into a fixed guild.
The message will be first sent in 4 hours. After that period will be randomly chosen
between 8 and 12 hours (after each send to all channels).

The message content is dynamically obtained through the get_data method of MyDynamicData.
The custom data class must inherit the TextMessageData class.
"""

# Import the necessary items
from daf.logging.logger_json import LoggerJSON

from daf.messagedata import FILE
from daf.messagedata.textdata import TextMessageData
from daf.messagedata.dynamicdata import DynamicMessageData
from datetime import timedelta
from daf.client import ACCOUNT
from daf.message.text_based import TextMESSAGE
from daf.message.messageperiod import RandomizedDurationPeriod
from daf.guild.guilduser import GUILD
from daf.logging.tracing import TraceLEVELS
import daf


# Define the logger
logger = LoggerJSON(
    path="./Logs/",
)


class MyDynamicData(DynamicMessageData):
    def __init__(self, backward: bool = False) -> None:
        self.data = [
            ("Look at this amazing dragon!", FILE(filename="my_dragon.png")),
            ("New blue dragon!", FILE(filename="my_dragon2.png")),
            ("Golden dragon. Limited!", FILE(filename="my_dragon3.png")),
        ]
        self.backward = backward

    def get_data(self):
        """
        Cycles through the list of self.data.
        """
        if self.backward:  # Pop from back, push to front
            index = -1  
            push_index = 0
        else:  # Pop from front, push to back
            index = 0
            push_index = len(self.data)

        text, file = self.data.pop(index)  # Take the next from cycle
        self.data.insert(push_index, (text, file))  # Put in the back of cycle

        return TextMessageData(text, files=[file])


# Defined accounts
accounts = [
    ACCOUNT(
        token="TOKEN",
        is_user=True,
        servers=[
            GUILD(
                snowflake=3213123123123123123213,
                messages=[
                    TextMESSAGE(
                        data=MyDynamicData(False),
                        channels=[55152351, 1312312415124],
                        period=RandomizedDurationPeriod(
                            minimum=timedelta(hours=8.0),
                            maximum=timedelta(hours=12.0),
                            next_send_time=timedelta(hours=4),
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
