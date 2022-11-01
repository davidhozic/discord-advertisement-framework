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
async def test_text_message_update():
    "This tests if all the text messages succeed in their sends"
    text_channels = []
    text_message = None
    direct_message = None
    guild = daf.get_guild_user(TEST_GUILD_ID)
    user = daf.get_guild_user(TEST_USER_ID)
    try:
        TEXT_MESSAGE_TEST_MESSAGE = [
            ("Hello world", daf.discord.Embed(title="Hello world")),
            ("Goodbye world", daf.discord.Embed(title="Goodbye world"))
        ]

        await daf.initialize(token=TEST_TOKEN)
        client = daf.get_client()
        dc_guild = client.get_guild(TEST_GUILD_ID)
        dc_test_cat = client.get_channel(TEST_CAT_CHANNEL_ID)

        # Create testing channels
        for i in range(1, TEST_CHANNEL_NUM + 1):
            text_channels.append(await dc_guild.create_text_channel(TEST_CHANNEL_FORMAT.format(i), category=dc_test_cat))

        # Create MESSAGE objects
        text_message = daf.message.TextMESSAGE(None, timedelta(seconds=5), "START", text_channels,
                                            "send", start_in=timedelta(), remove_after=None)

        direct_message = daf.message.DirectMESSAGE(None, timedelta(seconds=5), "START", "send",
                                                   start_in=timedelta(0), remove_after=None)

        # Initialize objects
        await guild.add_message(text_message)
        await user.add_message(direct_message)

        # TextMESSAGE send
        for data in TEXT_MESSAGE_TEST_MESSAGE:
            text, embed = data
            await text_message.update(data=data)
            result = await text_message._send()

            # Check results
            for message in text_message.sent_messages.values():
                assert text == message.content, "TextMESSAGE text does not match message content"
                assert embed.to_dict() in [e.to_dict() for e in message.embeds], "TextMESSAGE embed not in message embeds"

            assert len(result["channels"]["failed"]) == 0, "Failed to send to all channels"

            # DirectMESSAGE send
            await direct_message.update(data=data)
            result = await direct_message._send()

            # Check results
            message = direct_message.previous_message
            assert text == message.content, "DirectMESSAGE text does not match message content"
            assert embed.to_dict() in [e.to_dict() for e in message.embeds], "DirectMESSAGE embed not in message embeds"
            assert result["success_info"]["success"], "Failed to send to all channels"

    finally:
        for channel in text_channels:
            with suppress(daf.discord.HTTPException):
                await channel.delete()

        if text_message is not None:
            with suppress(ValueError):
                guild.remove_message(text_message)

        if direct_message is not None:
            with suppress(ValueError):
                user.remove_message(direct_message)



@pytest.mark.asyncio
async def test_voice_message_update():
    "This tests if all the voice messages succeed in their sends"
    voice_channels = []
    voice_message = None
    guild = daf.get_guild_user(TEST_GUILD_ID)
    try:
        VOICE_MESSAGE_TEST_MESSAGE = [
                (30, daf.AUDIO("https://www.youtube.com/watch?v=tWoo8i_VkvI")),
                (6, daf.AUDIO(os.path.join(os.path.dirname(os.path.abspath(__file__)), "testing123.mp3")))
            ]

        await daf.initialize(token=TEST_TOKEN)
        client = daf.get_client()
        dc_guild = client.get_guild(TEST_GUILD_ID)
        dc_test_cat = client.get_channel(TEST_CAT_CHANNEL_ID)

        # Create channels
        for i in range(1, TEST_CHANNEL_NUM + 1):
            voice_channels.append(await dc_guild.create_voice_channel(TEST_CHANNEL_FORMAT.format(i), category=dc_test_cat))

        voice_message = daf.message.VoiceMESSAGE(None, timedelta(seconds=20), daf.AUDIO("https://www.youtube.com/watch?v=dZLfasMPOU4"), voice_channels,
                                                volume=50, start_in=timedelta(), remove_after=None)
        
        await guild.add_message(voice_message)

        # Send
        for duration, audio in VOICE_MESSAGE_TEST_MESSAGE:
            await voice_message.update(data=audio)
            start_time = time.time()
            result = await voice_message._send()
            end_time = time.time()

            # Check results
            assert end_time - start_time >= duration * TEST_CHANNEL_NUM, "Message was not played till the end."
            assert len(result["channels"]["failed"]) == 0, "Failed to send to all channels"

    finally:
        for channel in voice_channels:
            with suppress(daf.discord.HTTPException):
                await channel.delete()

        if voice_message is not None:
            with suppress(ValueError):
                guild.remove_message(voice_message)
