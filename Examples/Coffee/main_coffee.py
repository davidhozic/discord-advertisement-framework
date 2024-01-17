"""
Description:
This is an example of an additional application layer you can build with this daf.
The application sends a message saying 'Good morning' every day at 10 AM and then sends a picture of a coffe cup from a randomized list.
"""
import os
import daf
import random
from datetime import datetime, timedelta

@daf.data_function
def get_data(storage: list):
    now = datetime.now()
    if not len(storage):
        storage += [os.path.join("./images", x) for x in os.listdir("./images")]
        random.shuffle(storage)

    image = storage.pop()
    text = "Good morning  ({:02d}.{:02d}.{:02d} - {:02d}:{:02d}:{:02d})".format(now.day, now.month,now.year,now.hour,now.minute, now.second)
    return text, daf.FILE(image) # Return message to be sent

now = datetime.now()
accounts = [
    daf.ACCOUNT(
        token="YOUR TOKEN",
        is_user=False,
        servers=[
            daf.GUILD(
                snowflake=123456789,
                messages=[

                    daf.TextMESSAGE(start_period=None, end_period=timedelta(days=1), data=get_data([]), channels=[123456789], mode="send", start_in=now.replace(second=0, microsecond=0, minute=0, hour=10) + timedelta(days=1) - now)
                ],
                logging=True
            )
        ]
    )
]


############################################################################################
daf.run(accounts=accounts)
                    
    