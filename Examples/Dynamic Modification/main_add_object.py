"""
The example shows how to dynamically add objects to the framework
after it had already been run.
"""
from datetime import timedelta
import daf


# Create a list in which we will automatically add guilds
allowed_strings = {"shill", "advert", "promo"}
data_to_shill = (     # Example data set
                "Hello World", 
                daf.discord.Embed(title="Example Embed",
                         color=daf.discord.Color.blue(),
                         description="This is a test embed")
                )

async def user_task():
    # Returns the client to send commands to discord, for more info about client see https://docs.pycord.dev/en/master/api.html?highlight=discord%20client#discord.Client
    account = daf.ACCOUNT(token="ASDASJDAKDK", is_user=False)
    guild = daf.GUILD(snowflake=123456)
    text_msg = daf.TextMESSAGE(None, timedelta(seconds=5), data_to_shill, [12345, 6789], "send", timedelta(seconds=0))

    # Dynamically add account
    await daf.add_object(account)
    
    # Dynamically add guild
    await account.add_server(guild) 
    # await daf.add_object(guild, account)

    # Dynamically add message
    await guild.add_message(text_msg)
    # await daf.add_object(text_msg, guild)


############################################################################################
if __name__ == "__main__":
    daf.run(user_callback=user_task)  
    