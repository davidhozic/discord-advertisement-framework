
"""
The example shows how to use the automatic responder feature.

DMResponder is used. It listens to messages inside DMs.
RegEx (regex) is used to match the text pattern.
MemberOfGuildConstraint is used for ensuring the author of the dm message is a member
of guild with ID 863071397207212052.
"""
# Import the necessary items
from _discord.flags import Intents
from daf.messagedata.textdata import TextMessageData
from daf.responder.constraints.dmconstraint import MemberOfGuildConstraint
from daf.client import ACCOUNT
from daf.responder.dmresponder import DMResponder
from daf.responder.actions.response import DMResponse
from daf.logic import regex
import daf


# Defined accounts
intents = Intents.default()
intents.members=True
intents.guild_messages=True
intents.dm_messages=True
intents.message_content=True

accounts = [
    ACCOUNT(
        token="CLIENT_TOKEN_HERE",
        is_user=False,
        intents=intents,
        responders=[
            DMResponder(
                condition=regex(
                    pattern="(buy|sell).*nft",
                ),
                action=DMResponse(
                    data=TextMessageData(
                        content="Instructions on how to buy / sell NFTs are provided on our official website:\nhttps://daf.davidhozic.com",
                    ),
                ),
                constraints=[
                    MemberOfGuildConstraint(
                        guild=863071397207212052,
                    ),
                ],
            ),
        ],
    ),
]

# Run the framework (blocking)
daf.run(
    accounts=accounts
)
