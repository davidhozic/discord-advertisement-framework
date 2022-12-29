"""
The following example uses a predefined list of messages to shill.
When the user task is run, it removes the message from the shill list dynamically.
"""
import daf

accounts = [
    account := daf.ACCOUNT(
        token="SDSADSDA87sd87",
        is_user=False,
        servers=[
            daf.GUILD(snowflake=213323123, messages=[]) # No messages as not needed for this demonstration
        ]
    )
]


async def user_task():
    guild = account.servers[0]
    await daf.remove_object(guild)


############################################################################################
if __name__ == "__main__":
    daf.run(user_callback=user_task, accounts=accounts)  
    