# Import the necessary items
from daf.logging._logging import LoggerJSON

from daf.guild import AutoGUILD
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
                logging=True,
                invite_track=[
                    "PQskxHzgsq",
                    "8u6kp7NmqK",
                    "ZE4bgRD2Um",
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
