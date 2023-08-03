"""
Testing module used to test the remote control server.
"""
from daf_gui.connector import RemoteConnectionCLIENT
from daf.misc import instance_track as it

import daf
import pytest
import asyncio


@pytest.mark.group_remote
@pytest.mark.asyncio
async def test_http(accounts):
    client = RemoteConnectionCLIENT("http://127.0.0.1", 8080, "Hello", "World")
    await client.initialize(debug=daf.TraceLEVELS.DEBUG)

    # Ping
    await client._ping()
    # Test get_logger
    assert await client.get_logger() is not None
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
    assert new_accounts == accounts


@pytest.mark.parametrize(
    "test_obj",
    [
        daf.ACCOUNT("BB"),
        daf.GUILD(1),
        daf.TextMESSAGE(None, 5, "Hello World", [1, 2]),
        daf.AutoCHANNEL("HH"),
        daf.AutoGUILD("test123"),
        daf.discord.Embed(color=daf.discord.Color.red()),
    ]
)
def test_remote_serialization(test_obj):
    def get_value(obj, att: str):
        custom_key_map = {
            asyncio.Semaphore: lambda sem: (sem.locked(), sem._value)
        }
        default_key = lambda x: x
        value = getattr(test_obj, attr, None)
        key = custom_key_map.get(type(value), default_key)
        return key(value)

    mapping = daf.convert_object_to_semi_dict(test_obj)
    test_obj_result = daf.convert_from_semi_dict(mapping)
    assert type(test_obj) is type(test_obj_result)
    for attr in daf.misc.get_all_slots(type(test_obj)):
        assert get_value(test_obj, attr) == get_value(test_obj_result, attr)
