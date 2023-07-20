# Import the necessary items
from daf.logging._logging import LoggerJSON

from daf.message.text_based import TextMESSAGE
from daf.guild import AutoGUILD
from daf.message.base import AutoCHANNEL
from datetime import timedelta
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
            AutoGUILD(
                include_pattern=".*",
                exclude_pattern="David's Dungeon",
                messages=[
                    TextMESSAGE(
                        start_period=None,
                        end_period=timedelta(
                            hours=2.0,
                        ),
                        data=[
                            "We are excited to announce...!",
                        ],
                        channels=AutoCHANNEL(
                            include_pattern="shill|advert|promo|projects",
                            exclude_pattern="vanilla-projects|ssfe-obvestila",
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
