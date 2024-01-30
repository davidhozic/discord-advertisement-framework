
from daf.responder.constraints import GuildConstraint, MemberOfGuildConstraint
from daf.logic import and_, or_, not_, regex, contains, BaseLogic
from daf.responder.actions import DMResponse, GuildResponse
from daf.responder import GuildResponder, DMResponder
from daf.messagedata import TextMessageData
from daf.client import ACCOUNT

import pytest


async def test_dm_responder():
    ...  # Can't test due to inability for bots to DM each other


@pytest.mark.parametrize(
    ("condition", "input", "should_match"),
    [
        # RegEx
        (regex("(buy|sell).*nft"), "I want to buy some nfts", True),
        (regex("(buy|sell).*nft"), "I want to sell some nfts", True),
        (regex("(buy|sell).*nft"), "I want to get some nfts", False),
        (regex("(buy|sell).*nft", full_match=True), "I want to buy some nfts", False),
        (regex("(buy|sell).*nft", full_match=True), "buy some nft", True),
        # Contains
        (contains('car'), "I want to buy a NFT", False),
        (contains('car'), "I want to buy a car", True),
        (contains('nfts'), "can I get some sweet NFTs my way please?", True),
        # Boolean mixed
        (and_(contains("buy"), contains("nfts"), contains("dragon")), "I want to buy some nfts.", False),
        (
            and_(contains("buy"), contains("nfts"), contains("dragon")),
            "I want to buy some nfts. I am interested in the dragon one.",
            True
        ),
        (
            and_(contains("buy"), contains("nfts"), contains("dragon")),
            "Cool dragon NFTs dude! Can I buy one?",
            True
        ),
        (
            and_(contains("buy"), contains("nft"), not_(contains("sell"))),
            "Can I buy the dragon NFT? I want to sell it after.",
            False
        ),
        (
            and_(contains("buy"), contains("nft"), not_(contains("sell"))),
            "Can I buy the dragon NFT? I want to use it after.",
            True
        ),
        (
            or_(
                and_(contains("give"), contains("green")),
                and_(contains("receive"), contains("blue"))
            ),
            "I want to receive the blue color.",
            True
        ),
        (
            or_(
                and_(contains("give"), contains("green")),
                and_(contains("receive"), contains("blue"))
            ),
            "I want to receive the green color.",
            False
        ),
        (
            or_(
                and_(contains("give"), contains("green")),
                and_(contains("receive"), contains("blue"))
            ),
            "I want to give the blue color.",
            False
        ),
        (
            or_(
                and_(contains("give"), contains("green")),
                and_(contains("receive"), contains("blue"))
            ),
            "I want to give the green color.",
            True
        ),
        (
            or_(
                and_(contains("give"), contains("green")),
                and_(contains("receive"), contains("blue"))
            ),
            "I want to give the green color. I also want to receive blue",
            True
        ),
        (
            or_(
                and_(contains("give"), contains("green")),
                and_(contains("receive"), contains("blue"))
            ),
            "I want to receive the green color. I also want to give blue",
            True
        ),
        (
            and_(regex("shill.*nft"), regex("advertise.*nft")),
            "Anyone knows where I can shill and advertise nft?",
            True
        ),
        (
            and_(regex("shill.*nft"), regex("advertise.*nft")),
            "Anyone knows where NFTs can shilled and advertised?",
            False
        )
    ]
)
def test_responder_conditions(condition: BaseLogic, input: str, should_match: bool):
    """
    Tests the text-matching condition logic.
    """
    assert condition.check(input.lower()) == should_match, "Condition failed"


async def test_guild_responder():
    ...  # Can't test guild responders as the second account is not joined in
