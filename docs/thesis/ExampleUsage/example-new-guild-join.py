# Import the necessary items
from daf.logging._logging import LoggerJSON

from daf.guild import AutoGUILD
from daf.web import QuerySortBy
from daf.web import QueryMembers
from daf.client import ACCOUNT
from daf.web import GuildDISCOVERY
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
        servers=[
            AutoGUILD(
                include_pattern=".*",
                auto_join=GuildDISCOVERY(
                    prompt="NFT",
                    sort_by=QuerySortBy.TEXT_RELEVANCY,
                    total_members=QueryMembers.B100_1k,
                    limit=15,
                ),
            ),
        ],
        username="ime.priimerk",
        password="geslo.moje",
    ),
]

# Run the framework (blocking)
daf.run(
    accounts=accounts,
    logger=logger,
    debug=TraceLEVELS.NORMAL,
    save_to_file=False
)
