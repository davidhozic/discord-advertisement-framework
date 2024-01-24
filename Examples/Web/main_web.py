
"""
Example shows login with email and password.
The AutoGUILD defines an auto_join parameter, which will be used to (semi) automatically
join new guilds based on a prompt. You as a user still need to solve any CAPTCHA challenges.
"""

# Import the necessary items
from daf.web import QueryMembers
from daf.client import ACCOUNT
from daf.web import GuildDISCOVERY
from daf.web import QuerySortBy
from daf.guild.autoguild import AutoGUILD
from daf.logging.tracing import TraceLEVELS
import daf


# Defined accounts
accounts = [
    ACCOUNT(
        servers=[
            AutoGUILD(
                include_pattern=".*",
                auto_join=GuildDISCOVERY(
                    prompt="NFT arts",
                    sort_by=QuerySortBy.TOP,
                    total_members=QueryMembers.B100_1k,
                    limit=30,
                ),
            ),
        ],
        username="username@email.com",
        password="password",
    ),
]

# Run the framework (blocking)
daf.run(
    accounts=accounts,
    debug=TraceLEVELS.NORMAL,
)
