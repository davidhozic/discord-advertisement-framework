"""
Testing module used to test the remote control server.
"""
from daf_gui.connector import RemoteConnectionCLIENT
from daf.misc import instance_track as it

import daf_gui.convert as daf_gui_convert

import daf
import pytest
import asyncio


@pytest.mark.parametrize(
    "test_obj",
    [
        daf.ACCOUNT("BB"),
        daf.GUILD(1),
        daf.TextMESSAGE(None, 5, "Hello World", [1, 2]),
        daf.AutoCHANNEL("HH"),
        daf.AutoGUILD("test123"),
        daf.discord.Embed(color=daf.discord.Color.red()),
        daf.SeleniumCLIENT("12345", "12345", None),
        daf.ACCOUNT(username="hello", password="world"),
        daf.VoiceMESSAGE(None, 5, daf.dtypes.FILE("Test", b'\xff\x51\x55'), daf.AutoCHANNEL("test"), 5, remove_after=5),
        None,
    ]
)
def test_remote_serialization(test_obj):
    def get_value(obj, attr: str):
        custom_key_map = {
            asyncio.Semaphore: lambda sem: (sem.locked(), sem._value)
        }
        default_key = lambda x: x
        value = getattr(test_obj, attr, None)
        key = custom_key_map.get(type(value), default_key)
        return key(value)

    def compare_objects(obj1, obj2):
        assert type(obj1) is type(obj2)
        for attr in daf.misc.get_all_slots(type(obj1)):
            assert get_value(obj1, attr) == get_value(obj2, attr)

    # Test manually created object_info
    if test_obj is None:
        object_info = daf_gui_convert.ObjectInfo(
            daf.LoggerSQL,
            {
                "username": None,
                "password": None,
                "server": "127.0.0.1",
                "port": 8080,
                "dialect": "sqlite",
                "fallback": None,
                "database": "testdb",
            }
        )
        object_from_object_info = daf_gui_convert.convert_to_objects(object_info)
        object_info_from_object = daf_gui_convert.convert_to_object_info(object_from_object_info)
        object_info_from_object.data["database"] = object_info_from_object.data["database"].replace(".db", "")
        assert object_info.data == object_info_from_object.data
        return

    # Test serialization for remote
    mapping = daf.convert_object_to_semi_dict(test_obj)
    test_obj_result = daf.convert_from_semi_dict(mapping)
    compare_objects(test_obj, test_obj_result)

    # Test class serialization for remote
    test_class = type(test_obj)
    mapping = daf.convert_object_to_semi_dict(test_class)
    test_class_result = daf.convert_from_semi_dict(mapping)
    assert test_class is test_class_result

    # Test serialization for GUI
    object_info_from_object = daf_gui_convert.convert_to_object_info(test_obj)
    object_from_object_info = daf_gui_convert.convert_to_objects(object_info_from_object)
    compare_objects(test_obj, object_from_object_info)


@pytest.mark.group_remote
@pytest.mark.asyncio
async def test_http(accounts, guilds):
    client = RemoteConnectionCLIENT("http://127.0.0.1", 8080, "Hello", "World")
    await client.initialize(debug=daf.TraceLEVELS.DEBUG)

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
    assert new_accounts == accounts
