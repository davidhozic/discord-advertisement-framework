"""
Tests remove_x methods and removal buffer.
"""
from datetime import timedelta
from typing import Tuple, List, Union

from daf.guild import GUILD, USER
from daf.message import TextMESSAGE, DirectMESSAGE

import pytest
import daf


TEST_USER_ID = 145196308985020416

@pytest.fixture(scope="module")
async def ACCOUNT(accounts: List[daf.ACCOUNT]):
    # Use a new account because we need a clean state here
    # and we cannot update the existing account due to bound API wrapper objects
    new_account = daf.ACCOUNT(accounts[0]._token)
    await new_account.initialize()
    yield new_account
    await new_account._close()


@pytest.fixture(scope="module")
async def GUILDSUSER(ACCOUNT: daf.ACCOUNT, guilds: Tuple[daf.discord.Guild]):
    account = ACCOUNT
    (g1, g2), u1 = guilds, await account.client.get_or_fetch_user(TEST_USER_ID)
    await account.add_server(GUILD(g1))
    await account.add_server(GUILD(g2))
    await account.add_server(USER(u1))
    yield account.servers
    for server in account.servers:
        await account.remove_server(server)


async def test_removal_servers(ACCOUNT: daf.ACCOUNT, GUILDSUSER: Tuple[Union[GUILD, USER]]):
    account = ACCOUNT
    account.removal_buffer_length = 1  # Cannot use the .update method due to fixtures being session dependant

    assert len(account.removed_servers) == 0

    G1, G2, U1 = GUILDSUSER

    await account.remove_server(G1)
    assert len(account.removed_servers) == 1
    assert G1 not in account.servers
    assert G1 in account.removed_servers

    await account.remove_server(G2)
    assert len(account.removed_servers) == 1
    assert G2 not in account.servers
    assert G2 in account.removed_servers

    await account.remove_server(U1)
    assert len(account.removed_servers) == 1
    assert U1 not in account.servers
    assert U1 in account.removed_servers

    account.removal_buffer_length = 3

    await account.add_server(G1)
    await account.add_server(G2)
    await account.add_server(U1)
    await account.remove_server(G1)
    await account.remove_server(G2)
    await account.remove_server(U1)
    rm_servers = account.removed_servers
    servers = account.servers
    assert len(rm_servers) == 3 and G1 in rm_servers and G2 in rm_servers and U1 in rm_servers \
        and G1 not in servers and G2 not in servers and U1 not in servers

    await account.add_server(G1)
    assert len(account.removed_servers) == 2 and G1 not in account.removed_servers
    await account.add_server(G2)
    assert len(account.removed_servers) == 1 and G2 not in account.removed_servers
    await account.add_server(U1)
    assert len(account.removed_servers) == 0


async def test_removal_messages(GUILDSUSER: Tuple[GUILD, GUILD, USER]):
    G1, _, U1 = GUILDSUSER

    await G1.update(removal_buffer_length=0)
    await U1.update(removal_buffer_length=0)

    await G1.add_message(TM := TextMESSAGE(None, timedelta(seconds=5), "Test", daf.AutoCHANNEL("test")))
    await U1.add_message(DM := DirectMESSAGE(None, timedelta(seconds=5), "Test"))

    for GG, MM in ((G1, TM), (U1, DM)):
        assert len(GG.removed_messages) == 0

        await GG.remove_message(MM)
        assert len(GG.removed_messages) == 0

        await GG.update(removal_buffer_length=1)

        await GG.add_message(MM)
        await GG.remove_message(MM)
        assert len(GG.removed_messages) == 1

        await GG.add_message(MM)
        assert len(GG.removed_messages) == 0
