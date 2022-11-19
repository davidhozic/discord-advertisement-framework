from datetime import timedelta
import daf


# STATIC DEFINITION
STATIC_AUTOGUILD_LIST = [
    daf.guild.AutoGUILD(
        include_pattern="NFT-Dragons", # Regex pattern of guild names that should be included
        exclude_pattern="NonFunctionalTesticle",   # Regex pattern of guild names that should be excluded
        remove_after=None, # Never stop automatically managing guilds
        messages=[ # Pre-include messages
            daf.message.TextMESSAGE(None, timedelta(seconds=5), "Buy our NFT today!",daf.guild.AutoCHANNEL("shill", "promo", timedelta(seconds=60)))
        ], 
        logging=True, # The generated GUILD objects will have logging enabled
        interval=timedelta(hours=1) # Scan for new guilds in a period of one hour
    )
]


async def main():
    # DYNAMIC DEFINITION/ADDITION
    auto_guild = daf.guild.AutoGUILD(
                    include_pattern="David", # Regex pattern of guild names that should be included
                    exclude_pattern="NFT-Python",   # Regex pattern of guild names that should be excluded
                    remove_after=None, # Never stop automatically managing guilds
                    messages=[], # Pre-include messages
                    logging=True, # The generated GUILD objects will have logging enabled
                    interval=timedelta(hours=1) # Scan for new guilds in a period of one hour
                )

    await daf.add_object(auto_guild)
    await auto_guild.add_message(
        daf.message.TextMESSAGE(
            None, timedelta(seconds=5), "Buy our NFT today!",
            daf.guild.AutoCHANNEL("shill", "promo", timedelta(seconds=60)))
    )



daf.run(
    token="SomeServerTokenHere",
    user_callback=main,
    server_list=STATIC_AUTOGUILD_LIST
)