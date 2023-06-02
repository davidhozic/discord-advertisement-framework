"""
Testing module used to test the remote control server.
"""
from daf_gui.connector import RemoteConnectionCLIENT

import daf
import pytest


@pytest.mark.asyncio
async def test_http(accounts):
    client = RemoteConnectionCLIENT("http://127.0.0.1", 8080, "Hello", "World")
    await client.initialize(debug=daf.TraceLEVELS.DEBUG)

    # Ping
    await client._ping()
    # Test get_logger
    assert await client.get_logger() is not None
    # Test object retrieval
    new_object = await client.refresh(accounts[0])
    assert new_object._daf_id == accounts[0]._daf_id
    # Test account removal
    await client.remove_account(accounts[0])
    await client.remove_account(accounts[1])
    # Test account addition
    await client.add_account(accounts[0])
    await client.add_account(accounts[1])

    # Test get_accounts
    new_accounts = await client.get_accounts()
    assert new_accounts == accounts
