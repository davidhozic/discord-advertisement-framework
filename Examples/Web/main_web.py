"""
This example shows how the user can use username and password to login into Discord and
it also shows how to configure the automatic guild discovery and join feature (auto_join parameter)
"""

from daf import QuerySortBy, QueryMembers
import daf

accounts = [
    daf.ACCOUNT(
        username="email@gmail.com",
        password="Password6745;*",
        servers=[
            daf.AutoGUILD(
                include_pattern=".*",
                auto_join=daf.GuildDISCOVERY(prompt="NFT arts",
                                             sort_by=QuerySortBy.TOP,
                                             total_members=QueryMembers.ALL,
                                             limit=20),
            ),
        ],
        proxy="protocol://ip:port"
    )
]


daf.run(
    accounts=accounts,
    debug=daf.TraceLEVELS.NORMAL
)
