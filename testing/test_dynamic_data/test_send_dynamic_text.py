import asyncio
from contextlib import suppress
from datetime import timedelta

import os

import pytest
# 
import daf


# SIMULATION
#
# CONFIGURATION
TEST_TOKEN = os.environ.get("DATT")
TEST_GUILD_ID = 863071397207212052
TEST_USER_ID = 145196308985020416
TEST_CAT_CHANNEL_ID = 1036585192275582997
TEST_CHANNEL_FORMAT = "pytest-{:02d}"
TEST_CHANNEL_NUM = 2


@pytest.mark.asyncio
async def test_text_message_send():
    "This tests if all the text messages succeed in their sends"
    text_channels = []
    try:
        @daf.data_function
        def dynamic_getter(items: list):
            return items.pop(0)

        data_ = [
            "Hello world", daf.discord.Embed(title="Hello world"),
            "Goodbye world", daf.discord.Embed(title="Goodbye world"),
            "Once upon a time", daf.discord.Embed(title="a few mistakes were made."),
            "I was in your sites"
        ]
        TEXT_MESSAGE_TEST_MESSAGE = dynamic_getter(data_.copy())
        DIRECT_MESSAGE_TEST_MESSAGE = dynamic_getter(data_.copy())
        

        await daf.initialize(token=TEST_TOKEN)
        client = daf.get_client()
        dc_guild = client.get_guild(TEST_GUILD_ID)
        dc_test_cat = client.get_channel(TEST_CAT_CHANNEL_ID)

        # Create testing channels
        for i in range(1, TEST_CHANNEL_NUM + 1):
            text_channels.append(await dc_guild.create_text_channel(TEST_CHANNEL_FORMAT.format(i), category=dc_test_cat))

        # Create GUILD
        guild = daf.GUILD(TEST_GUILD_ID)
        user = daf.USER(TEST_USER_ID)

        # Create MESSAGE objects
        text_message = daf.message.TextMESSAGE(None, timedelta(seconds=5), TEXT_MESSAGE_TEST_MESSAGE, text_channels,
                                            "send", start_in=timedelta(), remove_after=None)

        direct_message = daf.message.DirectMESSAGE(None, timedelta(seconds=5), DIRECT_MESSAGE_TEST_MESSAGE, "send",
                                                   start_in=timedelta(0), remove_after=None)

        # Initialize objects
        await guild.initialize()
        await user.initialize()
        await guild.add_message(text_message)
        await user.add_message(direct_message)


        # TextMESSAGE send
        for item in data_:
            result = await text_message._send()      
            text_message_datas = [(dc_msg.content, [x.to_dict() for x in dc_msg.embeds]) for dc_msg in text_message.sent_messages.values()]
            if isinstance(item, str):
                assert all(item == data[0] for data in text_message_datas), "TextMESSAGE text does not match message content"
            elif isinstance(item, daf.discord.Embed):
                embed = item.to_dict()
                assert all(embed in data[1] for data in text_message_datas), "TextMESSAGE embed not in message embeds"

            assert len(result["channels"]["failed"]) == 0, "Failed to send to all channels"

            # DirectMESSAGE send
            result = await direct_message._send()
            direct_message_data = (direct_message.previous_message.content, [x.to_dict() for x in direct_message.previous_message.embeds])
            if isinstance(item, str):
                assert item == direct_message_data[0], "DirectMESSAGE text does not match message content"
            elif isinstance(item, daf.discord.Embed):
                embed = item.to_dict()
                assert embed in direct_message_data[1], "DirectMESSAGE embed not in message embeds"

            assert result["success_info"]["success"], "Failed to send to all channels"

    finally:
        for channel in text_channels:
            with suppress(daf.discord.HTTPException):
                await channel.delete()