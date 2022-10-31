
from datetime import timedelta
from contextlib import suppress

import time
import os

import pytest
#
import daf


# SIMULATION
#


# CONFIGURATION
TEST_TOKEN = os.environ.get("DATT")
TEST_GUILD_ID = 863071397207212052
TEST_CAT_CHANNEL_ID = 1036585192275582997
TEST_CHANNEL_FORMAT = "pytest-{:02d}"
TEST_CHANNEL_NUM = 2

VOICE_MESSAGE_TEST_LENGTH = timedelta(seconds=10).total_seconds() # Test if entire message is played


@pytest.mark.asyncio
async def test_voice_message_send():
    "This tests if all the voice messages succeed in their sends"
    try:
        VOICE_MESSAGE_TEST_MESSAGE = daf.AUDIO("https://www.youtube.com/watch?v=dZLfasMPOU4") # 10 second countdown

        await daf.initialize(token=TEST_TOKEN)
        client = daf.get_client()
        dc_guild = client.get_guild(TEST_GUILD_ID)
        dc_test_cat = client.get_channel(TEST_CAT_CHANNEL_ID)

        # Create channels
        voice_channels = []
        for i in range(1, TEST_CHANNEL_NUM + 1):
            voice_channels.append(await dc_guild.create_voice_channel(TEST_CHANNEL_FORMAT.format(i), category=dc_test_cat))

        voice_message = daf.message.VoiceMESSAGE(None, timedelta(seconds=20), VOICE_MESSAGE_TEST_MESSAGE, voice_channels,
                                                volume=50, start_in=timedelta(), remove_after=None)
        
        # Initialize objects
        guild = daf.GUILD(TEST_GUILD_ID)
        await guild.initialize()
        await guild.add_message(voice_message)

        # Send
        start_time = time.time()
        result = await voice_message._send()
        end_time = time.time()

        # Check results
        assert end_time - start_time >= VOICE_MESSAGE_TEST_LENGTH * TEST_CHANNEL_NUM, "Message was not played till the end."
        assert len(result["channels"]["failed"]) == 0, "Failed to send to all channels"


    finally:
        for channel in voice_channels:
            with suppress(daf.discord.HTTPException):
                await channel.delete()