from daf.logging._logging import LoggerJSON
from daf.remote import RemoteAccessCLIENT
from daf.message.text_based import TextMESSAGE
from datetime import datetime
from daf.guild import GUILD
from _discord.embeds import Embed
from daf.client import ACCOUNT
from _discord.embeds import EmbedField
from daf.message.base import AutoCHANNEL
from _discord.colour import Colour
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
)

# Defined accounts
accounts = [
  ACCOUNT(
    token="OTKMSMDASKNKLSADHJASJDHASLJ..."
    servers=[
      GUILD(
        snowflake=1038102918714372206,
        messages=[
          TextMESSAGE(
            start_period=None,
            end_period=999999999,
            data=[
              Embed(
                color=Colour(
                  value=15519507,
                ),
                title="[Delo] Poletni tabot...",
                url="https://fe.uni-lj.si/solarji...",
                description="Na Fakulteti za Elek...",
                fields=[
                  EmbedField(
                    name="Kdaj",
                    value="21. 8. do 25. 8. na FE.",
                    inline=True,
                  ),
                  EmbedField(
                    name="Plačilo",
                    value="Urna postavka je 10 € bruto.",
                    inline=True,
                  ),
                  EmbedField(
                    name="Prijave",
                    value="Če te to delo zanima, jim ...",
                  ),
                ],
              ),
            ],
            channels=AutoCHANNEL(
              include_pattern="obvestila",
            ),
            start_in=datetime(
              year=2023,
              month=7,
              day=12,
              hour=10,
              minute=0,
            ),
            remove_after=1,
          ),
        ],
        logging=True,
      ),
    ],
  ),
]

# Run the framework (blocking)
daf.run(
  accounts=accounts,
  logger=logger,
  debug=TraceLEVELS.NORMAL,
  remote_client=remote_client,
  save_to_file=False
)
