"""
Description:
This is an example of an additional application layer you can build with this framework.
The application sends a message saying 'Good morning' every day at 10 AM and then sends a picture of a coffe cup from a randomized list.
"""
from datetime import timedelta
import daf
import app.app
from daf import discord




servers = [
    daf.GUILD(
        snowflake=123456789,
        messages=[

            daf.TextMESSAGE(start_period=None, end_period=timedelta(seconds=10), data=app.app.get_data(), channels=[123456789], mode="send", start_in=timedelta(seconds=0))
        ],
        logging=True
    )
]


############################################################################################
daf.run(  token="YOUR TOKEN", server_list=servers)
                    
    