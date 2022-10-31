
from datetime import timedelta
from contextlib import suppress

import time
import os

import pytest
import asyncio
#
import daf

# SIMULATION
#

# CONFIGURATION
TEST_TOKEN = os.environ.get("DATT")
TEST_GUILD_ID = 863071397207212052
TEST_CAT_CHANNEL_ID = 1036585192275582997
TEST_CHANNEL_FORMAT = "pytest-{:02d}"
TEST_CHANNEL_NUM = 1


@pytest.mark.asyncio
async def test_voice_message_update():
    "This tests if all the voice messages succeed in their sends"
    voice_channels = []
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
        
        # Initialize objects
        guild = daf.GUILD(TEST_GUILD_ID)
        await guild.initialize()
        await guild.add_message(voice_message)

        # Send
        for data in VOICE_MESSAGE_TEST_MESSAGE:
            duration, audio = data
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

