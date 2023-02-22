from datetime import timedelta, datetime

import pytest
import daf
import shutil
import os
import pathlib
import json

TEST_USER_ID = 145196308985020416
C_FILE_NAME_FORBIDDEN_CHAR = ('<','>','"','/','\\','|','?','*',":")


@pytest.mark.asyncio
async def test_logging_json(channels, guilds, accounts):
    "Test if json logging works"
    account = accounts[0]
    dc_guild, _ = guilds
    text_channels, _ = channels
    try:
        json_logger = daf.LoggerJSON("./History")
        await json_logger.initialize()
        daf.logging._set_logger(json_logger)

        guild = daf.GUILD(dc_guild, logging=True)
        await guild.initialize(parent=account)
        guild_context = guild.generate_log_context()
        await guild.add_message(tm := daf.TextMESSAGE(None, timedelta(seconds=5), data="Hello World", channels=text_channels))

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
                message_history = result_json["message_history"]
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
            result = await tm._send() 
            message_ctx = result.message_context
            await daf.logging.save_log(guild_context, message_ctx)
            check_json_results(message_ctx)
    finally:
        shutil.rmtree("./History", ignore_errors=True)


@pytest.mark.asyncio
async def test_logging_sql(channels, guilds, accounts):
    """
    Tests if SQL logging works(only sqlite).
    It does not test any of the results as it assumes the database
    will raise an exception if anything is wrong.
    """
    account = accounts[0]
    dc_guild, _ = guilds
    text_channels, _ = channels
    try:
        sql_logger = daf.LoggerSQL(database="testdb")
        await sql_logger.initialize()
        daf.logging._set_logger(sql_logger)
        guild = daf.GUILD(dc_guild, logging=True)
        await guild.initialize(parent=account)
        guild_context = guild.generate_log_context()
        await guild.add_message(tm := daf.TextMESSAGE(None, timedelta(seconds=5), data="Hello World", channels=text_channels))

        data = [
            "Hello World",
            (daf.discord.Embed(title="Test"), "ABCD"),
            (daf.discord.Embed(title="Test2"), "ABCDEFU"),
        ]

        for d in data:
            await tm.update(data=d)
            result = await tm._send()
            message_ctx = result.message_context
            await daf.logging.save_log(guild_context, message_ctx)
    finally:
        os.remove("./testdb.db")
