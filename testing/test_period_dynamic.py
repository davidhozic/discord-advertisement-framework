from contextlib import suppress
from datetime import timedelta

import asyncio
import time
import pytest
import daf

# SIMULATION

# CONFIGURATION
TEST_GUILD_ID = 863071397207212052
TEST_USER_ID = 145196308985020416
TEST_SEND_PERIOD_TEXT = timedelta(seconds=6)
TEST_SEND_PERIOD_VOICE = timedelta(seconds=10)
TEST_PERIOD_MAX_VARIATION = 0.12 # Relative variation from period allowed
TEST_MAX_WAIT_TIME = 15 # Maximum wait for message



@pytest.mark.asyncio
async def test_text_period(text_channels):
    "Tests if the period and dynamic data works"
    guild = daf.GUILD(TEST_GUILD_ID)
    user = daf.USER(TEST_USER_ID)
    try:
        await daf.add_object(guild)
        await daf.add_object(user)
        
        @daf.data_function
        def dynamic_getter(items: list):
            item = items.pop(0)
            items.append(item)
            return item

        @daf.data_function
        async def dynamic_getter_async(items: list):
            item = items.pop(0)
            items.append(item)
            return item
            
        data_ = [
            "Hello world", daf.discord.Embed(title="Hello world"),
            "Goodbye world", daf.discord.Embed(title="Goodbye world"),
        ]
        TEXT_MESSAGE_TEST_MESSAGE = dynamic_getter(data_.copy())
        DIRECT_MESSAGE_TEST_MESSAGE = dynamic_getter_async(data_.copy())

        await asyncio.sleep(10) # Clears rate limit
        client = daf.get_client()

        # Preparation
        test_period_secs = TEST_SEND_PERIOD_TEXT.total_seconds()
        bottom_secs = (test_period_secs * (1 - TEST_PERIOD_MAX_VARIATION))
        upper_secs = (test_period_secs * (1 + TEST_PERIOD_MAX_VARIATION))
        wait_for_message = lambda: client.wait_for("message", 
                                                    check=lambda message: 
                                                          message.author.id == client.user.id
                                                          and message.channel == text_channels[0],
                                                          timeout=TEST_MAX_WAIT_TIME)
        # Test TextMESSAGE
        text_message = daf.message.TextMESSAGE(None, TEST_SEND_PERIOD_TEXT, TEXT_MESSAGE_TEST_MESSAGE, [text_channels[0]],
                                            "send", start_in=TEST_SEND_PERIOD_TEXT, remove_after=None)
        await guild.add_message(text_message)
        for item in data_:
            start = time.time()
            result: daf.discord.Message = await wait_for_message()
            content, embeds = (result.content, [x.to_dict() for x in result.embeds])
            end = time.time()
            # Check period
            assert bottom_secs < (end - start) < upper_secs
            # Check data
            if isinstance(item, str):
                assert item == content, "TextMESSAGE text does not match message content"
            elif isinstance(item, daf.discord.Embed):
                assert item.to_dict() in embeds, "TextMESSAGE embed not in message embeds"

        guild.remove_message(text_message)
        await asyncio.sleep(10) # Clears rate limit
        # Test DirectMESSAGE
        direct_message = daf.message.DirectMESSAGE(None, TEST_SEND_PERIOD_TEXT, DIRECT_MESSAGE_TEST_MESSAGE, "send",
                                                   start_in=TEST_SEND_PERIOD_TEXT, remove_after=None)
        await user.add_message(direct_message)
        wait_for_message = lambda: client.wait_for("message",
                                            check=lambda message: 
                                                    message.author.id == client.user.id 
                                                    and message.channel.id == user.apiobject.dm_channel.id,
                                                    timeout=TEST_MAX_WAIT_TIME)
        for item in data_:
            start = time.time()
            result: daf.discord.Message = await wait_for_message()
            content, embeds = (result.content, [x.to_dict() for x in result.embeds])
            end = time.time()
            # Check period
            assert bottom_secs < (end - start) < upper_secs 
            # Check data
            if isinstance(item, str):
                assert item == content, "DirectMESSAGE text does not match message content"
            elif isinstance(item, daf.discord.Embed):
                assert item.to_dict() in embeds, "DirectMESSAGE embed not in message embeds"
        
    finally:
        with suppress(ValueError):
            daf.remove_object(guild)
        with suppress(ValueError):
            daf.remove_object(user)
        

@pytest.mark.asyncio
async def test_voice_period(voice_channels):
    "Tests if the period and dynamic data works"
    guild = daf.GUILD(TEST_GUILD_ID)
    user = daf.USER(TEST_USER_ID)
    try:
        await asyncio.sleep(10)

        @daf.data_function
        def dynamic_getter(items: list):
            item = items.pop(0)
            items.append(item)
            return item[1]

        await daf.add_object(guild)
        await daf.add_object(user)
        data_ = [
            (5, daf.AUDIO("https://www.youtube.com/watch?v=IGQBtbKSVhY")),
            (3, daf.AUDIO("https://www.youtube.com/watch?v=1O0yazhqaxs"))
        ]
        VOICE_MESSAGE_TEST_MESSAGE = dynamic_getter(data_.copy())
        guild = daf.get_guild_user(TEST_GUILD_ID)
        client = daf.get_client()

        test_period_secs = TEST_SEND_PERIOD_VOICE.total_seconds()
        bottom_secs = (test_period_secs * (1 - TEST_PERIOD_MAX_VARIATION))
        upper_secs = (test_period_secs * (1 + TEST_PERIOD_MAX_VARIATION))
        wait_for_message = lambda: client.wait_for("voice_state_update", check=lambda member, before, after: before.channel is None and member.id == client.user.id and after.channel == voice_channels[0], timeout=TEST_MAX_WAIT_TIME)

        # Test VoiceMESSAGE
        voice_message = daf.message.VoiceMESSAGE(None, TEST_SEND_PERIOD_VOICE, VOICE_MESSAGE_TEST_MESSAGE, [voice_channels[0]],
                                                volume=50, start_in=TEST_SEND_PERIOD_VOICE, remove_after=None)
        await guild.add_message(voice_message)
        for item in data_:
            start = time.time()
            await wait_for_message()
            end = time.time()
            assert bottom_secs < (end - start) < upper_secs

    finally:
        with suppress(ValueError):
            daf.remove_object(guild)
        with suppress(ValueError):
            daf.remove_object(user)