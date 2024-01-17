from daf.responder.constraints import GuildConstraint, MemberOfGuildConstraint
from daf.responder.logic import and_, or_, not_, regex, contains
from daf.responder.actions import DMResponse, GuildResponse
from daf.responder import GuildResponder, DMResponder
from daf import discord

import pytest
import daf


async def test_guild_responder(accounts: tuple[daf.ACCOUNT, daf.ACCOUNT], guilds: discord.Guild):
    account1, account2 = accounts


async def test_dm_responder():
    ...  # TODO