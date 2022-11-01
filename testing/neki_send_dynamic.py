import asyncio
from contextlib import suppress
from datetime import timedelta

import os
import time

import pytest
# 
import daf


# SIMULATION
#
# CONFIGURATION
TEST_TOKEN = os.environ.get("DISCORD_TOKEN")
TEST_GUILD_ID = 863071397207212052
TEST_USER_ID = 145196308985020416
TEST_CAT_CHANNEL_ID = 1036585192275582997
TEST_CHANNEL_FORMAT = "pytest-{:02d}"
TEST_CHANNEL_NUM = 2


@pytest.mark.asyncio
async def test_text_message_send():
    "This tests if all the text messages succeed in their sends"
    text_channels = []
    guild = daf.get_guild_user(TEST_GUILD_ID)
    user = daf.get_guild_user(TEST_USER_ID)
    text_message = None
    direct_message = None
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
        
        client = daf.get_client()
        dc_guild = client.get_guild(TEST_GUILD_ID)
        dc_test_cat = client.get_channel(TEST_CAT_CHANNEL_ID)

        # Create testing channels
        for i in range(1, TEST_CHANNEL_NUM + 1):
            text_channels.append(await dc_guild.create_text_channel(TEST_CHANNEL_FORMAT.format(i), category=dc_test_cat))

        # Create MESSAGE objects
        text_message = daf.message.TextMESSAGE(None, timedelta(seconds=5), TEXT_MESSAGE_TEST_MESSAGE, text_channels,
                                            "send", start_in=timedelta(), remove_after=None)

        direct_message = daf.message.DirectMESSAGE(None, timedelta(seconds=5), DIRECT_MESSAGE_TEST_MESSAGE, "send",
                                                   start_in=timedelta(0), remove_after=None)

        # Initialize objects
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
        
        with suppress(ValueError):
            if text_message is not None:
                guild.remove_message(text_message)
        with suppress(ValueError):
            if direct_message is not None:
                user.remove_message(direct_message)



@pytest.mark.asyncio
async def test_voice_message_send():
    "This tests if all the voice messages succeed in their sends"
    
    voice_channels = []
    voice_message = None
    guild = daf.get_guild_user(TEST_GUILD_ID)
    try:
        await daf.initialize(token=TEST_TOKEN)
        client = daf.get_client()
        dc_guild = client.get_guild(TEST_GUILD_ID)
        dc_test_cat = client.get_channel(TEST_CAT_CHANNEL_ID)

        @daf.data_function
        def dynamic_getter(items: list):
            return items.pop(0)[1]

        data_ = [
            (6, daf.dtypes.AUDIO(os.path.join(os.path.dirname(os.path.abspath(__file__)), "testing123.mp3"))),
            (30, daf.dtypes.AUDIO("https://www.youtube.com/watch?v=tWoo8i_VkvI"))
        ]
        VOICE_MESSAGE_TEST_MESSAGE = dynamic_getter(data_.copy())

        # Create channels
        for i in range(1, TEST_CHANNEL_NUM + 1):
            voice_channels.append(await dc_guild.create_voice_channel(TEST_CHANNEL_FORMAT.format(i), category=dc_test_cat))

        voice_message = daf.message.VoiceMESSAGE(None, timedelta(seconds=20), VOICE_MESSAGE_TEST_MESSAGE, voice_channels,
                                                volume=50, start_in=timedelta(), remove_after=None)
        

        await guild.add_message(voice_message)
        for length, audio in data_:
            # Send
            start_time = time.time()
            result = await voice_message._send()
            end_time = time.time()

            # Check results
            assert end_time - start_time >= length * TEST_CHANNEL_NUM, "Message was not played till the end."
            assert len(result["channels"]["failed"]) == 0, "Failed to send to all channels"

    finally:
        for channel in voice_channels:
            with suppress(daf.discord.HTTPException):
                await channel.delete()

        with suppress(ValueError):
            if voice_message is not None:
                guild.remove_message(voice_message)