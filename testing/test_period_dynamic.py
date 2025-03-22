from contextlib import suppress
from datetime import timedelta
from typing import List, Tuple, Union

from daf.events import *

import asyncio
import time
import pytest
import daf
import os

# SIMULATION

# CONFIGURATION
TEST_USER_ID = 145196308985020416
TEST_SEND_PERIOD_TEXT = timedelta(seconds=10)
TEST_SEND_PERIOD_VOICE = timedelta(seconds=10)
TEST_PERIOD_MAX_VARIATION = 0.12 # Relative variation from period allowed
TEST_MAX_WAIT_TIME = 15  # Maximum wait for message


@pytest.fixture(scope="module")
async def GUILD(guilds, accounts: List[daf.ACCOUNT]):
    guild = daf.GUILD(guilds[0], logging=True)
    await accounts[0].add_server(guild)
    yield guild
    await accounts[0].remove_server(guild)


@pytest.fixture(scope="module")
async def USER(accounts: List[daf.ACCOUNT]):
    guild = daf.USER(TEST_USER_ID, logging=True)
    await accounts[0].add_server(guild)
    yield guild
    await accounts[0].remove_server(guild)


async def test_text_period(GUILD: daf.GUILD, USER: daf.USER, channels):
    "Tests if the period and dynamic data works"
    client: daf.discord.Client = GUILD.parent.client
    text_channels = channels[0]

    guild = GUILD
    user = USER
    
    class SyncDynamicData(daf.DynamicMessageData):
        def __init__(self, items: list):
            super().__init__()
            self.items = items
        
        def get_data(self):
            item = self.items.pop(0)
            self.items.append(item)
            return item

    class AsyncDynamicData(daf.DynamicMessageData):
        def __init__(self, items: list):
            super().__init__()
            self.items = items

        async def get_data(self):
            item = self.items.pop(0)
            self.items.append(item)
            return item

    data_ = [
        daf.TextMessageData("Hello world", daf.discord.Embed(title="Hello world")),
        daf.TextMessageData("Goodbye world", daf.discord.Embed(title="Goodbye world")),
    ]
    TEXT_MESSAGE_TEST_MESSAGE = SyncDynamicData(data_.copy())
    DIRECT_MESSAGE_TEST_MESSAGE = AsyncDynamicData(data_.copy())

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
    assert len(guild.parent.servers) == 2
    await asyncio.sleep(10)
    text_message = daf.message.TextMESSAGE(
        period=daf.FixedDurationPeriod(TEST_SEND_PERIOD_TEXT, next_send_time=TEST_SEND_PERIOD_TEXT),
        data=TEXT_MESSAGE_TEST_MESSAGE,
        channels=[text_channels[0]]
    )
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

    await guild.remove_message(text_message)
    await asyncio.sleep(10)
    # Test DirectMESSAGE
    direct_message = daf.message.DirectMESSAGE(
        period=daf.FixedDurationPeriod(TEST_SEND_PERIOD_TEXT, next_send_time=TEST_SEND_PERIOD_TEXT),
        data=DIRECT_MESSAGE_TEST_MESSAGE,
    )
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


async def test_voice_period(
    channels: Tuple[List[Union[daf.discord.TextChannel, daf.discord.VoiceChannel]]],
    GUILD: daf.GUILD
):
    "Tests if the period and dynamic data works"
    client: daf.discord.Client = GUILD.parent.client
    voice_channels = channels[1]
    guild = GUILD
    
    class AsyncDynamicData(daf.DynamicMessageData):
        def __init__(self, items: list):
            super().__init__()
            self.items = items

        async def get_data(self):
            item = self.items.pop(0)
            self.items.append(item)
            return item

    cwd = os.getcwd()
    os.chdir(os.path.dirname(__file__))
    data_ = [
        daf.VoiceMessageData(daf.FILE("testing123.mp3"))
    ]
    VOICE_MESSAGE_TEST_MESSAGE = AsyncDynamicData(data_.copy())
    os.chdir(cwd)

    test_period_secs = TEST_SEND_PERIOD_VOICE.total_seconds()
    bottom_secs = (test_period_secs * (1 - TEST_PERIOD_MAX_VARIATION))
    upper_secs = (test_period_secs * (1 + TEST_PERIOD_MAX_VARIATION))
    wait_for_message = lambda: client.wait_for("voice_state_update", check=lambda member, before, after: before.channel is None and member.id == client.user.id and after.channel == voice_channels[0], timeout=TEST_MAX_WAIT_TIME)

    # Test VoiceMESSAGE
    await asyncio.sleep(10)
    voice_message = daf.message.VoiceMESSAGE(
        period=daf.FixedDurationPeriod(TEST_SEND_PERIOD_VOICE, TEST_SEND_PERIOD_VOICE),
        data=VOICE_MESSAGE_TEST_MESSAGE,
        channels=[voice_channels[0]],
        volume=50
    )
    await guild.add_message(voice_message)
    for item in data_:
        start = time.time()
        await wait_for_message()
        end = time.time()
        assert bottom_secs < (end - start) < upper_secs
