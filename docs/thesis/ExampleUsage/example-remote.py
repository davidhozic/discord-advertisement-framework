# Import the necessary items
from daf.logging._logging import LoggerJSON
from daf.remote import RemoteAccessCLIENT

from daf.logging.tracing import TraceLEVELS
import daf

# Define the logger
logger = LoggerJSON(
    path="C:\\Users\\David\\daf\\History",
)

# Define remote control context
remote_client = RemoteAccessCLIENT(
    host="0.0.0.0",
    port=80,
    username="ime",
    password="geslo",
)

# Defined accounts
accounts = [
]

# Run the framework (blocking)
daf.run(
    accounts=accounts,
    logger=logger,
    debug=TraceLEVELS.NORMAL,
    remote_client=remote_client,
    save_to_file=False
)
