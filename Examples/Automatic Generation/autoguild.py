from datetime import timedelta
import daf


# STATIC DEFINITION
ACCOUNTS = [
    daf.ACCOUNT(
        token="SomeToken",
        is_user=False,
        servers=[
            daf.guild.AutoGUILD( include_pattern="NFT-Dragons", # Regex pattern of guild names that should be included
                                 exclude_pattern="NonFunctionalTesticle",   # Regex pattern of guild names that should be excluded
                                 remove_after=None, # Never stop automatically managing guilds
                                 messages=[
                                    daf.message.TextMESSAGE(None, timedelta(seconds=5), "Buy our NFT today!", daf.message.AutoCHANNEL("shill", "promo", timedelta(seconds=60)))
                                 ], 
                                 logging=True, # The generated GUILD objects will have logging enabled
                                 interval=timedelta(hours=1) ) # Scan for new guilds in a period of one hour
        ]
    )
]



daf.run(
    accounts=ACCOUNTS
)