# Import the necessary items
from daf.logging import LoggerSQL, LoggerJSON
from daf.guild import GUILD
from datetime import timedelta
from daf.client import ACCOUNT
from daf.message.base import AutoCHANNEL
from daf.message.text_based import TextMESSAGE
from daf.logging.tracing import TraceLEVELS
import daf


rolls = [
    "https://i.pinimg.com/originals/b7/fb/80/b7fb80122cf46d0e584f3a0768aef282.gif",
    "https://bit.ly/3sHrjQZ",
    "https://static.wikia.nocookie.net/a1dea591-8a10-4c02-a573-5321c601c129",
    "https://www.gifcen.com/wp-content/uploads/2022/03/rickroll-gif-4.gif",
    "https://bit.ly/3u5D8Dt",
    "http://static1.squarespace.com/static/60503ac20951e15087fbe7b8/60504609ee9c445722c9dd4e/60e3f9b541eb1b01e8e46854/1627103366283/RalphRoll.gif?format=1500w",
    "https://i.imgflip.com/56bhvt.gif",
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
]


@daf.data_function
def get(st):
    item = st.pop(0)
    st.append(item)
    return item


# Define the logger
logger = LoggerSQL(
    dialect="mysql",
    database="mydatabase",
    fallback=LoggerJSON(path="History")
)

# Defined accounts
accounts = [
    ACCOUNT(
        token="OTA5MzgyNDE3MDg3ODgxMjc2.YZDeXw.34V-TbQSsxJxx8Fu399Mafu8jDI",
        is_user=False,
        intents=None,
        proxy=None,
        servers=[
            GUILD(
                snowflake=863071397207212052,
                messages=[
                    TextMESSAGE(
                        start_period=None,
                        end_period=timedelta(
                            seconds=5.0,
                        ),
                        data=get(rolls),
                        channels=AutoCHANNEL(
                            include_pattern="test",
                        ),
                    ),
                ],
                logging=True,
                remove_after=None,
                invite_track=[
                    "5fYEEpak",
                    "WxWdjKMp",
                    "qDvbRF7C",
                ],
            ),
        ],
    ),
]

# Run the framework (blocking)
daf.run(
    accounts=accounts,
    logger=logger,
    debug=TraceLEVELS.NORMAL
)
