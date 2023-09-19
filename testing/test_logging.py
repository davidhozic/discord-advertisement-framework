from datetime import timedelta, datetime
from typing import List

from daf.events import *

import pytest
import daf
import shutil
import os
import pathlib
import json

TEST_USER_ID = 145196308985020416
C_FILE_NAME_FORBIDDEN_CHAR = ('<','>','"','/','\\','|','?','*',":")


@pytest.fixture(scope="module")
async def TEXT_MESSAGE(channels, guilds, accounts: List[daf.ACCOUNT]):
    guild = daf.GUILD(guilds[0], logging=True)
    await accounts[0].add_server(guild)
    guild._event_ctrl.remove_listener(EventID.message_ready, guild._advertise)
    await guild.add_message(tm := daf.TextMESSAGE(None, timedelta(seconds=5), data="Hello World", channels=channels[0]))
    yield tm
    await accounts[0].remove_server(guild)


async def test_logging_json(TEXT_MESSAGE: daf.TextMESSAGE):
    "Test if json logging works"
    tm = TEXT_MESSAGE
    try:
        json_logger = daf.LoggerJSON("./History")
        await json_logger.initialize()
        daf.logging._logging._set_logger(json_logger)

        guild_context = tm.parent.generate_log_context()
        account_context = tm.parent.parent.generate_log_context()

        def check_json_results(message_context):
            timestruct = datetime.now()
            logging_output = (pathlib.Path(json_logger.path)
                            .joinpath("{:02d}".format(timestruct.year))
                            .joinpath("{:02d}".format(timestruct.month))
                            .joinpath("{:02d}".format(timestruct.day)))

            logging_output.mkdir(parents=True,exist_ok=True)
            logging_output = logging_output.joinpath("".join(char if char not in C_FILE_NAME_FORBIDDEN_CHAR
                                                                else "#" for char in guild_context["name"]) + ".json")
            # Check results
            with open(str(logging_output)) as reader:
                result_json = json.load(reader)
                # Check guild data
                for k, v in guild_context.items():
                    assert result_json[k] == v, "Resulting data does not match the guild_context"
                
                # Check message data
                message_history = result_json["message_tracking"][str(account_context["id"])]["messages"]
                message_history = message_history[0] # Get only last send data
                message_history.pop("index")
                message_history.pop("timestamp")
                assert message_history == message_context # Should be exact match


        data = [
            "Hello World",
            (daf.discord.Embed(title="Test"), "ABCD"),
            (daf.discord.Embed(title="Test2"), "ABCDEFU"),
        ]

        for d in data:
            await tm.update(data=d)
            message_ctx = await tm._send() 
            await daf.logging.save_log(guild_context, message_ctx, account_context)
            check_json_results(message_ctx)

        # Simulate member join without checking data
        await daf.logging.save_log(
            guild_context,
            invite_context={"id": "ABCDE", "member": {"id": 123456789, "name": "test"}}
        )
    finally:
        shutil.rmtree("./History", ignore_errors=True)


async def test_logging_sql(TEXT_MESSAGE: daf.TextMESSAGE):
    """
    Tests if SQL logging works(only sqlite).
    It does not test any of the results as it assumes the database
    will raise an exception if anything is wrong.
    """
    tm = TEXT_MESSAGE
    try:
        sql_logger = daf.LoggerSQL(database="testdb")
        await sql_logger.initialize()
        daf.logging._logging._set_logger(sql_logger)

        guild_context = tm.parent.generate_log_context()
        account_context = tm.parent.parent.generate_log_context()

        data = [
            "Hello World",
            (daf.discord.Embed(title="Test"), "ABCD"),
            (daf.discord.Embed(title="Test2"), "ABCDEFU"),
        ]

        for d in data:
            await tm.update(data=d)
            message_ctx = await tm._send()
            await daf.logging.save_log(guild_context, message_ctx, account_context)

        # Simulate member join without checking data
        await daf.logging.save_log(
            guild_context,
            invite_context={"id": "ABCDE", "member": {"id": 123456789, "name": "test"}}
        )
    finally:
        os.remove("./testdb.db")
        daf.logging._logging._set_logger(None)
