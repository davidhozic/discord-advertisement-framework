# Import the necessary items
from daf.logging.logger_json import LoggerJSON

from daf.client import ACCOUNT
from daf.logic import contains
from daf.guild.autoguild import AutoGUILD
from daf.logic import or_
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
            AutoGUILD(
                include_pattern=or_(
                    operands=[
                        contains(keyword="shill"),
                        contains(keyword="NFT"),
                        contains(keyword="dragon"),
                        contains(keyword="promo"),
                    ],
                ),
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
