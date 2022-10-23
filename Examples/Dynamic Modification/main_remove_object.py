"""
The following example uses a predefined list of messages to shill.
When the user task is run, it removes the message from the shill list dynamically.
"""
import daf

servers = [
    daf.GUILD(snowflake=213323123, messages=[]) # No messages as not needed for this demonstration
]


async def user_task():
    daf.trace("Removing the GUILD")
    guild = servers[0]
    await daf.remove_object(guild)
    daf.trace("Finished")


############################################################################################
if __name__ == "__main__":
    daf.run(token="OOFOAFO321o3oOOAOO$Oo$o$@O4242",
            user_callback=user_task,
            server_list=servers)  
    