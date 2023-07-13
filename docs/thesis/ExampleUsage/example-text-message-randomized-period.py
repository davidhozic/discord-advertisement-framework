
# Import the necessary items
from daf.logging._logging import LoggerJSON

from daf.message.text_based import TextMESSAGE
from daf.guild import GUILD
from datetime import timedelta
from datetime import datetime
from daf.client import ACCOUNT
from daf.logging.tracing import TraceLEVELS
import daf

# Define the logger
logger = LoggerJSON(
    path="C:\\Users\\David\\daf\\History",
)

# Define remote control context


# Defined accounts
accounts = [
    ACCOUNT(
        token="OTMHH72GFA7213JSDH2131HJb",
        is_user=True,
        servers=[
            GUILD(
                snowflake=123456789,
                messages=[
                    TextMESSAGE(
                        start_period=timedelta(
                            hours=1.0,
                        ),
                        end_period=timedelta(
                            hours=2.0,
                        ),
                        data="We are excited to announce the launch of our White Rabbit NFT project!",
                        channels=[
                            2313213123123123123123123,
                            9876652312312431232323277,
                        ],
                        start_in=datetime(
                            year=2023,
                            month=7,
                            day=13,
                        ),
                        remove_after=5,
                    ),
                ],
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
