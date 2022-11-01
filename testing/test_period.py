import asyncio
from contextlib import suppress
from datetime import timedelta

import os
import time

import pytest
import pytest_asyncio
# 
import daf


# SIMULATION
#os.environ["DISCORD_TOKEN"] = "OTM2NzM5NDMxMDczODY1Nzg5.G0f9I1.JxEOmOcDvWdp9zcvG9uV-8fZIKpQ6HqDm_q3Rk"

# CONFIGURATION
TEST_TOKEN = os.environ.get("DISCORD_TOKEN")
TEST_GUILD_ID = 863071397207212052
TEST_USER_ID = 145196308985020416
TEST_CAT_CHANNEL_ID = 1036585192275582997
TEST_CHANNEL_FORMAT = "pytest-{:02d}"
TEST_SEND_PERIOD_TEXT = timedelta(seconds=5)
TEST_SEND_PERIOD_VOICE = timedelta(seconds=7)
TEST_PERIOD_MAX_VARIATION = 0.10 # Relative variation from period allowed
TEST_MAX_WAIT_TIME = 15 # Maximum wait for message
TEST_NUM = 2 # How many times to test



@pytest.mark.asyncio
async def test_text_period():
    "This tests if all the text messages succeed in their sends"
    text_channel = None
    guild = daf.get_guild_user(TEST_GUILD_ID)
    user = daf.get_guild_user(TEST_USER_ID)
    try:
        TEXT_MESSAGE_TEST_MESSAGE = "Hello world", daf.discord.Embed(title="Hello world")
        await asyncio.sleep(5) # Clears rate limit
        client = daf.get_client()
        dc_guild = client.get_guild(TEST_GUILD_ID)
        dc_test_cat = client.get_channel(TEST_CAT_CHANNEL_ID)

        # Create testing channels
        text_channel = await dc_guild.create_text_channel(TEST_CHANNEL_FORMAT.format(1), category=dc_test_cat)

        # Test TextMESSAGE
        text_message = daf.message.TextMESSAGE(None, TEST_SEND_PERIOD_TEXT, TEXT_MESSAGE_TEST_MESSAGE, [text_channel],
                                            "send", start_in=TEST_SEND_PERIOD_TEXT, remove_after=None)
        await guild.add_message(text_message)

        test_period_secs = TEST_SEND_PERIOD_TEXT.total_seconds()
        bottom_secs = (test_period_secs * (1 - TEST_PERIOD_MAX_VARIATION))
        upper_secs = (test_period_secs * (1 + TEST_PERIOD_MAX_VARIATION))
        wait_for_message = lambda: client.wait_for("message", check=lambda message: message.author.id == client.user.id and message.channel == text_channel, timeout=TEST_MAX_WAIT_TIME)


        await wait_for_message()
        for i in range(TEST_NUM):
            start = time.time()
            await wait_for_message()
            end = time.time()
            assert bottom_secs < (end - start) < upper_secs

        guild.remove_message(text_message)
        # Test DirectMESSAGE
        direct_message = daf.message.DirectMESSAGE(None, TEST_SEND_PERIOD_TEXT, TEXT_MESSAGE_TEST_MESSAGE, "send",
                                                   start_in=TEST_SEND_PERIOD_TEXT, remove_after=None)
        await user.add_message(direct_message)
        wait_for_message = lambda: client.wait_for("message", check=lambda message: message.author.id == client.user.id and dm_channel == message.channel, timeout=TEST_MAX_WAIT_TIME)
        dm_channel = user.apiobject.dm_channel

        await wait_for_message()
        for i in range(TEST_NUM):
            start = time.time()
            await wait_for_message()
            end = time.time()
            assert bottom_secs < (end - start) < upper_secs

    finally:
        if text_channel is not None:
            with suppress(daf.discord.HTTPException):
                await text_channel.delete()
        
        with suppress(ValueError):
            if text_message is not None:
                guild.remove_message(text_message)
        with suppress(ValueError):
            if direct_message is not None:
                user.remove_message(direct_message)
        

@pytest.mark.asyncio
async def test_voice_period():
    "This tests if all the text messages succeed in their sends"
    voice_channel = None
    try:
        VOICE_MESSAGE_TEST_MESSAGE = daf.AUDIO("https://www.youtube.com/watch?v=IGQBtbKSVhY")
        guild = daf.get_guild_user(TEST_GUILD_ID)
        await asyncio.sleep(5) # Clears rate limit
        client = daf.get_client()
        dc_guild = client.get_guild(TEST_GUILD_ID)
        dc_test_cat = client.get_channel(TEST_CAT_CHANNEL_ID)

        # Create testing channels
        voice_channel = await dc_guild.create_voice_channel(TEST_CHANNEL_FORMAT.format(1), category=dc_test_cat)

        # Test VoiceMESSAGE
        voice_message = daf.message.VoiceMESSAGE(None, TEST_SEND_PERIOD_VOICE, VOICE_MESSAGE_TEST_MESSAGE, [voice_channel],
                                                volume=50, start_in=TEST_SEND_PERIOD_VOICE, remove_after=None)
        await guild.add_message(voice_message)

        test_period_secs = TEST_SEND_PERIOD_VOICE.total_seconds()
        bottom_secs = (test_period_secs * (1 - TEST_PERIOD_MAX_VARIATION))
        upper_secs = (test_period_secs * (1 + TEST_PERIOD_MAX_VARIATION))
        wait_for_message = lambda: client.wait_for("voice_state_update", check=lambda member, before, after: before.channel is None and member.id == client.user.id and after.channel == voice_channel, timeout=TEST_MAX_WAIT_TIME)


        await wait_for_message()
        for i in range(TEST_NUM):
            start = time.time()
            await wait_for_message()
            end = time.time()
            assert bottom_secs < (end - start) < upper_secs

    finally:
        if voice_channel is not None:
            with suppress(daf.discord.HTTPException):
                await voice_channel.delete()