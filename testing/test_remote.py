"""
Testing module used to test the remote control server.
"""
from daf_gui.connector import RemoteConnectionCLIENT
from daf.misc import instance_track as it
from test_util import *

import daf
import pytest


@pytest.mark.group_remote
async def test_http(accounts, guilds):
    client = RemoteConnectionCLIENT("http://127.0.0.1", 8080, "Hello", "World")
    await client.initialize(debug=daf.TraceLEVELS.DEPRECATED)

    # Ping
    await client._ping()

    # Test get_logger
    # assert (await client.get_logger()) is not None

    # Execute method
    await client.execute_method(
        it.ObjectReference(it.get_object_id(accounts[0])),
        "add_server",
        server=daf.GUILD(guilds[0].id)
    )
    new_object = await client.refresh(it.ObjectReference(it.get_object_id(accounts[0])))
    assert len(new_object.servers) == 1

    await client.execute_method(
        it.ObjectReference(it.get_object_id(new_object)),
        "remove_server",
        server=it.ObjectReference(it.get_object_id(new_object.servers[0]))
    )
    new_object = await client.refresh(it.ObjectReference(it.get_object_id(accounts[0])))
    assert len(new_object.servers) == 0

    # Test object retrieval
    new_object = await client.refresh(it.ObjectReference(it.get_object_id(accounts[0])))
    assert new_object._daf_id == accounts[0]._daf_id
    # Test account removal
    await client.remove_account(it.ObjectReference(it.get_object_id(accounts[0])))
    await client.remove_account(it.ObjectReference(it.get_object_id(accounts[1])))
    # Test account addition
    await client.add_account(accounts[0])
    await client.add_account(accounts[1])

    # Test get_accounts
    new_accounts = await client.get_accounts()
    for i in range(len(new_accounts)):
        compare_objects(new_accounts[i], accounts[i], {"_deleted", "_client", "_daf_id", "_ws_task"})
