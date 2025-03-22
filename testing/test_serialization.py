
from datetime import datetime, timedelta
from test_util import *
from tkclasswiz.convert import convert_to_object_info, convert_to_objects, ObjectInfo

import daf_gui
import pytest
import daf

@pytest.mark.parametrize(
    "test_obj",
    [
        daf.ACCOUNT("BB"),
        daf.GUILD(1),
        daf.TextMESSAGE(period=daf.FixedDurationPeriod(timedelta(seconds=5)), data=daf.TextMessageData("Hello World"), channels=[1, 2]),
        daf.AutoCHANNEL(daf.regex("HH")),
        daf.AutoGUILD(daf.regex("test123")),
        daf.discord.Embed(color=daf.discord.Color.red()),
        daf.SeleniumCLIENT("12345", "12345"),
        daf.ACCOUNT(username="hello", password="world"),
        daf.VoiceMESSAGE(period=daf.FixedDurationPeriod(timedelta(seconds=5)), data=daf.VoiceMessageData(daf.FILE("Test", b'\xff\x51\x55')), channels=daf.AutoCHANNEL("test"), volume=5, remove_after=5),
        daf.DMResponder(
            daf.logic.regex("nft.*buy"),
            daf.DMResponse(daf.TextMessageData("Hello")),
            [daf.MemberOfGuildConstraint(32323)]
        ),
        daf.GuildResponder(
            daf.or_(daf.contains("hello"), daf.contains("world")),
            daf.GuildResponse(daf.TextMessageData("Goodbye")),
            [daf.GuildConstraint(32323)]
        )
    ]
)
def test_remote_serialization(test_obj):
    """
    Test tests the object to dict serialization and reverse.
    Additionally it tests serialization from object into ObjectInfo (live view on GUI).
    """
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
    object_info_from_object = convert_to_object_info(test_obj)
    object_from_object_info = convert_to_objects(object_info_from_object)
    compare_objects(test_obj, object_from_object_info)


@pytest.mark.parametrize(
    "object_info, expected_object",
    [
        (ObjectInfo(daf.LoggerSQL, {"database": "testdb"}), daf.LoggerSQL(database="testdb")),
        (ObjectInfo(daf.LoggerJSON, {}), daf.LoggerJSON()),
        (ObjectInfo(datetime, {"year": 2022, "month": 1, "day": 1}), datetime(2022, 1, 1)),
        (ObjectInfo(timedelta, {"seconds": 5}), timedelta(seconds=5)),
        (ObjectInfo(daf.discord.Intents, {"guilds": False}), daf.discord.Intents(guilds=False)),
    ]
)
def test_object_info_to_object(object_info: ObjectInfo, expected_object: object):
    """
    Test checks conversion from ObjectInfo into an object and back.
    """
    created_object = convert_to_objects(object_info)
    compare_objects(created_object, expected_object)
